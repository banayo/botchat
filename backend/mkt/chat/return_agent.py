from functools import lru_cache
from threading import Lock, local
import logging
import types

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from sqlalchemy import text

from ai_config import llm
from db.oracle import get_oracle_engine
from mkt import RETURN_VIEW_NAME, VIEW_OWNER
from mkt.chat.metadata import RETURN_VALUE_CONTEXT, build_mkt_return_prompt
from mkt.chat.sql_guard import SQLPolicyError, validate_and_limit_sql

logger = logging.getLogger("uvicorn.error")
_agent_lock = Lock()
_state = local()


def _set_last_result(value: dict | None) -> None:
    _state.last_result = value


def _get_last_result() -> dict | None:
    return getattr(_state, "last_result", None)


def _patched_get_table_info_no_throw(self, table_names=None):
    try:
        schema = self.get_table_info(table_names)
        return schema + "\n\n" + RETURN_VALUE_CONTEXT
    except ValueError as exc:
        return f"Error: {exc}"


def _patched_run_no_throw(self, command, *args, **kwargs):
    try:
        safe_sql = validate_and_limit_sql(command, view_name=RETURN_VIEW_NAME)
    except SQLPolicyError as exc:
        logger.warning("mkt return SQL rejected: %s | original=%s", exc, command)
        return f"Error: SQL rejected by policy: {exc}"
    logger.info("mkt return SQL executing:\n%s", safe_sql)
    try:
        with self._engine.connect() as conn:
            if self._schema and self.dialect == "oracle":
                conn.exec_driver_sql(f"ALTER SESSION SET CURRENT_SCHEMA = {self._schema}")
            cursor = conn.execute(text(safe_sql))
            columns = list(cursor.keys())
            rows = [list(row) for row in cursor.fetchall()]
    except Exception as exc:
        logger.warning("mkt return SQL failed: %s", exc)
        return f"Error: {exc}"
    _set_last_result({"sql": safe_sql, "columns": columns, "rows": rows})
    return str([tuple(row) for row in rows])


def create_mkt_return_sql_database() -> SQLDatabase:
    engine = get_oracle_engine("mkt")
    db = SQLDatabase(
        engine,
        schema=VIEW_OWNER,
        view_support=True,
        sample_rows_in_table_info=0,
        include_tables=[RETURN_VIEW_NAME.lower()],
    )
    db.get_table_info_no_throw = types.MethodType(_patched_get_table_info_no_throw, db)
    db.run_no_throw = types.MethodType(_patched_run_no_throw, db)
    return db


@lru_cache(maxsize=1)
def get_mkt_return_agent():
    logger.info("Initializing marketing return LangChain agent view=%s", RETURN_VIEW_NAME)
    return create_sql_agent(
        llm=llm,
        db=create_mkt_return_sql_database(),
        agent_type="tool-calling",
        prefix=build_mkt_return_prompt(),
        top_k=50,
        max_iterations=8,
        max_execution_time=90,
        handle_parsing_errors=True,
        verbose=False,
    )


def invoke_mkt_return_agent(question: str) -> dict:
    logger.info("mkt return agent invoke start: %s", question[:300])
    agent = get_mkt_return_agent()
    _set_last_result(None)
    with _agent_lock:
        result = agent.invoke({"input": question})
    result["data"] = _get_last_result()
    logger.info("mkt return agent invoke done")
    return result
