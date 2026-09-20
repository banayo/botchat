import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from db.oracle import get_oracle_engine
from mkt.report.models import MktReportRequest
from mkt.report.query_builder import build_mkt_report_sql

logger = logging.getLogger("uvicorn.error")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def execute_mkt_report(request: MktReportRequest) -> dict[str, Any]:
    sql, params = build_mkt_report_sql(request)
    logger.info("mkt report SQL:\n%s\nparams=%s", sql, params)
    engine = get_oracle_engine("mkt")
    with engine.connect() as connection:
        result = connection.execute(text(sql), params)
        columns = list(result.keys())
        rows = [
            {col: _json_safe(row[idx]) for idx, col in enumerate(columns)}
            for row in result.fetchall()
        ]

    return {
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "summary": _compact_summary(request, columns, rows),
    }


def _compact_summary(
    request: MktReportRequest,
    columns: list[str],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    totals = [row.get("METRIC_VALUE") for row in rows if row.get("METRIC_VALUE") is not None]
    numeric = [float(value) for value in totals]
    summary: dict[str, Any] = {
        "metric": request.metric,
        "aggregation": request.aggregation,
        "row_count": len(rows),
        "total": round(sum(numeric), 2) if numeric else 0,
    }
    if "MONTH_KEY" in columns:
        summary["periods"] = len({row.get("MONTH_KEY") for row in rows})
    if "ZONE" in columns:
        zones = {row.get("ZONE") for row in rows if row.get("ZONE") is not None}
        summary["zones"] = len(zones)
    return summary
