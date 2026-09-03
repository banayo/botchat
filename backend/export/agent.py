from inspect import signature
from functools import lru_cache
from threading import Lock

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase

from ai_config import llm
from db.oracle import get_oracle_engine
from export.metadata import CURATED_VALUE_CONTEXT, build_export_prompt
from export.sql_guard import SQLPolicyError, validate_and_limit_sql

_agent_lock = Lock()


class OracleExportSQLDatabase(SQLDatabase):
    def get_table_info(self, table_names=None):
        if table_names is not None:
            names = [table_names] if isinstance(table_names, str) else list(table_names)
            by_upper = {name.upper(): name for name in self.get_usable_table_names()}
            resolved = []
            missing = []
            for name in names:
                actual = by_upper.get(str(name).upper())
                if actual is None:
                    missing.append(name)
                else:
                    resolved.append(actual)
            if missing:
                raise ValueError(f"table_names {set(missing)} not found in database")
            table_names = resolved

        kwargs = {}
        if "get_col_comments" in signature(super().get_table_info).parameters:
            kwargs["get_col_comments"] = True
        return super().get_table_info(table_names, **kwargs)

    def get_table_info_no_throw(self, table_names=None):
        try:
            schema = self.get_table_info(table_names)
            return schema + "\n\n" + CURATED_VALUE_CONTEXT
        except ValueError as exc:
            return f"Error: {exc}"

    def run_no_throw(self, command, *args, **kwargs):
        try:
            safe_sql = validate_and_limit_sql(command)
        except SQLPolicyError as exc:
            return f"Error: SQL rejected by policy: {exc}"
        return super().run_no_throw(safe_sql, *args, **kwargs)


def create_export_sql_database() -> OracleExportSQLDatabase:
    engine = get_oracle_engine()
    base = {
        "schema": "KMPROD",
        "view_support": True,
        "sample_rows_in_table_info": 0,
    }
    for table_name in ("exp$erp_sale_rep_exp", "EXP$ERP_SALE_REP_EXP"):
        try:
            return OracleExportSQLDatabase(
                engine,
                include_tables=[table_name],
                **base,
            )
        except ValueError:
            continue

    db = OracleExportSQLDatabase(engine, **base)
    matched = next(
        (
            name
            for name in db.get_usable_table_names()
            if name.upper() == "EXP$ERP_SALE_REP_EXP"
        ),
        "exp$erp_sale_rep_exp",
    )
    db._all_tables.add(matched)
    db._include_tables = {matched}
    return db


@lru_cache(maxsize=1)
def get_export_agent():
    oracle_db = create_export_sql_database()
    kwargs = {
        "llm": llm,
        "db": oracle_db,
        "agent_type": "tool-calling",
        "top_k": 50,
        "max_iterations": 6,
        "max_execution_time": 90,
        "handle_parsing_errors": True,
        "verbose": False,
    }
    if "prefix" in signature(create_sql_agent).parameters:
        kwargs["prefix"] = build_export_prompt()
    return create_sql_agent(**kwargs)


def invoke_export_agent(question: str) -> dict:
    agent = get_export_agent()
    payload = {"input": question}
    if "prefix" not in signature(create_sql_agent).parameters:
        payload["input"] = f"{build_export_prompt()}\n\nคำถามจากผู้ใช้: {question}"
    with _agent_lock:
        return agent.invoke(payload)
