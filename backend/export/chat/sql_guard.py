import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from export import AGENT_ROW_CAP, VIEW_NAME, VIEW_OWNER

class SQLPolicyError(Exception):
    pass


_FORBIDDEN_NODES = tuple(
    node
    for node in (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Create,
        exp.Alter,
        exp.Command,
        getattr(exp, "Grant", None),
        getattr(exp, "Merge", None),
        getattr(exp, "TruncateTable", None),
    )
    if node is not None
)
_FORBIDDEN_FUNC_PREFIXES = ("DBMS_", "UTL_", "SYS.")
_VIEW_PATTERN = re.compile(
    rf"\b(?:{re.escape(VIEW_OWNER)}\.)?{re.escape(VIEW_NAME)}\b",
    re.IGNORECASE,
)


def _ident(node) -> str:
    if node is None:
        return ""
    if isinstance(node, str):
        return node.replace('"', "").upper()
    name = getattr(node, "name", None) or getattr(node, "this", None)
    if name is None:
        return str(node).replace('"', "").upper()
    if hasattr(name, "name"):
        return str(name.name).replace('"', "").upper()
    return str(name).replace('"', "").upper()


def _quote_approved_view(sql: str) -> str:
    return _VIEW_PATTERN.sub(f'"{VIEW_NAME}"', sql)


def _reject_forbidden_functions(tree: exp.Expression) -> None:
    for func in tree.find_all(exp.Anonymous):
        name = _ident(func.this)
        if any(name.startswith(prefix) for prefix in _FORBIDDEN_FUNC_PREFIXES):
            raise SQLPolicyError(f"function {name} is not allowed")
        if name in {"EXECUTE", "CALL"}:
            raise SQLPolicyError(f"function {name} is not allowed")


def _assert_approved_tables(tree: exp.Expression) -> None:
    tables = list(tree.find_all(exp.Table))
    if not tables:
        raise SQLPolicyError("query must read from the approved export view")

    for table in tables:
        name = _ident(table.this)
        schema = _ident(table.args.get("db"))
        catalog = _ident(table.args.get("catalog"))
        if catalog:
            raise SQLPolicyError("database links are not allowed")
        if schema and schema != VIEW_OWNER:
            raise SQLPolicyError(f"schema {schema} is not allowed")
        if name != VIEW_NAME:
            raise SQLPolicyError(f"table {name} is not allowed")


def validate_and_limit_sql(sql_query: str, row_cap: int = AGENT_ROW_CAP) -> str:
    if not sql_query or not str(sql_query).strip():
        raise SQLPolicyError("SQL is empty")

    raw = str(sql_query).strip().rstrip(";").strip()
    if not raw:
        raise SQLPolicyError("SQL is empty")
    if ";" in raw:
        raise SQLPolicyError("multiple statements are not allowed")
    if "@" in raw:
        raise SQLPolicyError("database links are not allowed")

    upper = raw.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise SQLPolicyError("only SELECT or WITH ... SELECT is allowed")

    to_parse = _quote_approved_view(raw)
    try:
        statements = sqlglot.parse(to_parse, dialect="oracle")
    except ParseError as exc:
        raise SQLPolicyError(f"unable to parse SQL: {exc}") from exc

    trees = [stmt for stmt in statements if stmt is not None]
    if len(trees) != 1:
        raise SQLPolicyError("exactly one SQL statement is required")

    tree = trees[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Except, exp.Intersect)):
        raise SQLPolicyError("only SELECT or WITH ... SELECT is allowed")

    for node_type in _FORBIDDEN_NODES:
        if tree.find(node_type):
            raise SQLPolicyError("DML/DDL is not allowed")

    if tree.find(exp.Fetch) or tree.find(exp.Offset) or tree.find(exp.Limit):
        raise SQLPolicyError(
            "FETCH FIRST / OFFSET / LIMIT are not allowed; use ROWNUM on Oracle 11g"
        )
    if "FETCH FIRST" in upper or " OFFSET " in f" {upper} ":
        raise SQLPolicyError(
            "FETCH FIRST / OFFSET / LIMIT are not allowed; use ROWNUM on Oracle 11g"
        )

    _assert_approved_tables(tree)
    _reject_forbidden_functions(tree)

    cap = int(row_cap)
    if cap < 1:
        raise SQLPolicyError("row cap must be positive")

    return f"SELECT * FROM (\n{raw}\n) WHERE ROWNUM <= {cap}"
