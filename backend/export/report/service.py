import logging
from decimal import Decimal
from typing import Any
from sqlalchemy import text
from db.oracle import get_oracle_engine
from export.report.models import ExportReportRequest# Pydantic model
from export.report.query_builder import build_export_report_sql

logger = logging.getLogger("uvicorn.error")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def execute_export_report(request: ExportReportRequest) -> dict[str, Any]: # Pydantic → registry → SQL builder → Oracle
    sql, params = build_export_report_sql(request) # ส่ง request ไปยัง query_builder.py
    logger.info("export report SQL:\n%s\nparams=%s", sql, params)
    engine = get_oracle_engine()
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
    request: ExportReportRequest,
    columns: list[str],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    totals = [row.get("metric_value") for row in rows if row.get("metric_value") is not None]
    numeric = [float(value) for value in totals]
    summary: dict[str, Any] = {
        "metric": request.metric,
        "aggregation": request.aggregation,
        "row_count": len(rows),
        "total": round(sum(numeric), 2) if numeric else 0,
    }
    if "month_key" in columns:
        summary["periods"] = len({row.get("month_key") for row in rows})
    if "country" in columns:
        countries = {row.get("country") for row in rows if row.get("country") is not None}
        summary["countries"] = len(countries)
        if numeric and rows:
            top = max(rows, key=lambda row: float(row.get("metric_value") or 0))
            summary["highest_country"] = top.get("country")
    return summary
