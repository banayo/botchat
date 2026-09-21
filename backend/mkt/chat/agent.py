from functools import lru_cache
from threading import Lock, local
import logging
import types

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from sqlalchemy import text

from ai_config import llm
from db.oracle import get_oracle_engine
from mkt import VIEW_NAME, VIEW_OWNER
from mkt.chat.metadata import CURATED_VALUE_CONTEXT, build_mkt_prompt
from mkt.chat.sql_guard import SQLPolicyError, validate_and_limit_sql

logger = logging.getLogger("uvicorn.error")
_agent_lock = Lock()

# AgentExecutor only returns {"input", "output"} — the raw rows are dropped.
# _patched_run_no_throw stashes them here so the route can return real data
# instead of the agent's prose summary.
#
# Must be thread-local, NOT a ContextVar: langchain_core's BaseTool.run executes
# tools via copy_context().run(...), so a ContextVar.set() inside the tool is
# discarded when it returns. Same thread throughout, so thread-local survives.
_state = local()


def _set_last_result(value: dict | None) -> None:
    _state.last_result = value


def _get_last_result() -> dict | None:
    return getattr(_state, "last_result", None)


def _patched_get_table_info_no_throw(self, table_names=None):
    try:
        schema = self.get_table_info(table_names)
        return schema + "\n\n" + CURATED_VALUE_CONTEXT
    except ValueError as exc:
        return f"Error: {exc}"


def _patched_run_no_throw(self, command, *args, **kwargs):
    try:
        safe_sql = validate_and_limit_sql(command)
    except SQLPolicyError as exc:
        logger.warning("mkt SQL rejected: %s | original=%s", exc, command)
        return f"Error: SQL rejected by policy: {exc}"
    logger.info("mkt SQL executing:\n%s", safe_sql)
    try:
        with self._engine.connect() as conn:
            # SQLDatabase._execute does this for us; we bypass it to keep the
            # cursor, so the agent's unqualified table names still resolve.
            if self._schema and self.dialect == "oracle":
                conn.exec_driver_sql(f"ALTER SESSION SET CURRENT_SCHEMA = {self._schema}")
            cursor = conn.execute(text(safe_sql))
            columns = list(cursor.keys())
            rows = [list(row) for row in cursor.fetchall()]
    except Exception as exc:  # keep the agent loop alive, same as run_no_throw
        logger.warning("mkt SQL failed: %s", exc)
        return f"Error: {exc}"
    _set_last_result({"sql": safe_sql, "columns": columns, "rows": rows})
    # string form the agent expects as a tool observation
    return str([tuple(row) for row in rows])


def create_mkt_sql_database() -> SQLDatabase:
    engine = get_oracle_engine("mkt")
    table_name = VIEW_NAME.lower()
    db = SQLDatabase(
        engine,
        schema=VIEW_OWNER,
        view_support=True,
        sample_rows_in_table_info=0,
        include_tables=[table_name],
    )
    db.get_table_info_no_throw = types.MethodType(_patched_get_table_info_no_throw, db)
    db.run_no_throw = types.MethodType(_patched_run_no_throw, db)
    return db


@lru_cache(maxsize=1)
def get_mkt_agent():
    logger.info("Initializing marketing LangChain agent (Oracle + vLLM)")
    return create_sql_agent(
        llm=llm,
        db=create_mkt_sql_database(),
        agent_type="tool-calling",
        prefix=build_mkt_prompt(),
        top_k=50,
        max_iterations=8,
        max_execution_time=90,
        handle_parsing_errors=True,
        verbose=False,
    )

    
def invoke_mkt_agent(question: str) -> dict:
    logger.info("mkt agent invoke start: %s", question[:300])
    agent = get_mkt_agent()
    # pool threads are reused: clear on entry so a rejected/failed query in this
    # request can never return the previous request's rows
    _set_last_result(None)
    with _agent_lock:
        result = agent.invoke({"input": question})
    result["data"] = _get_last_result()
    logger.info("mkt agent invoke done")
    return result
