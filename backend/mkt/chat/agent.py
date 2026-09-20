from inspect import signature
from functools import lru_cache
from threading import Lock
import logging
import types

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase

from ai_config import llm
from db.oracle import get_oracle_engine
from mkt import VIEW_NAME, VIEW_OWNER
from mkt.chat.metadata import CURATED_VALUE_CONTEXT, build_mkt_prompt
from mkt.chat.sql_guard import SQLPolicyError, validate_and_limit_sql

logger = logging.getLogger("uvicorn.error")
_agent_lock = Lock()


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
    return SQLDatabase.run_no_throw(self, safe_sql, *args, **kwargs)


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
    oracle_db = create_mkt_sql_database()
    kwargs = {
        "llm": llm,
        "db": oracle_db,
        "agent_type": "tool-calling",
        "top_k": 50,
        "max_iterations": 8,
        "max_execution_time": 90,
        "handle_parsing_errors": True,
        "verbose": False,
    }
    if "prefix" in signature(create_sql_agent).parameters:
        kwargs["prefix"] = build_mkt_prompt()
    return create_sql_agent(**kwargs)


def invoke_mkt_agent(question: str) -> dict:
    logger.info("mkt agent invoke start: %s", question[:300])
    agent = get_mkt_agent()
    payload = {"input": question}
    if "prefix" not in signature(create_sql_agent).parameters:
        payload["input"] = f"{build_mkt_prompt()}\n\nคำถามจากผู้ใช้: {question}"
    with _agent_lock:
        result = agent.invoke(payload)
    logger.info("mkt agent invoke done")
    return result
