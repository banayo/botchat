import calendar
import logging
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from db.oracle import get_oracle_engine
from mkt.report.models import MktReportRequest, MktYoyRequest
from mkt.report.query_builder import build_mkt_report_sql
from mkt.report.registry import MKT_DIMENSIONS

logger = logging.getLogger("uvicorn.error")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _shift_year(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        # 29 Feb → 28 Feb
        return value.replace(year=value.year + years, day=28)


def yoy_period_ranges(
    mode: str,
    as_of: date,
) -> tuple[date, date, date, date]:
    """Return (current_from, current_to, prior_from, prior_to) inclusive dates."""
    month_start = as_of.replace(day=1)
    if mode == "full_month_yoy":
        last_day = calendar.monthrange(as_of.year, as_of.month)[1]
        current_to = as_of.replace(day=last_day)
        prior_from = _shift_year(month_start, -1)
        prior_to = _shift_year(current_to, -1)
        return month_start, current_to, prior_from, prior_to

    # mtd_yoy (default): 1st of month → as_of vs same span last year
    prior_to = _shift_year(as_of, -1)
    prior_from = prior_to.replace(day=1)
    return month_start, as_of, prior_from, prior_to


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
        "date_from": request.date_from.isoformat(),
        "date_to": request.date_to.isoformat(),
        "row_count": len(rows),
        "total": round(sum(numeric), 2) if numeric else 0,
    }
    if "MONTH_KEY" in columns:
        summary["periods"] = len({row.get("MONTH_KEY") for row in rows})
    if "CUST_CHANNEL" in columns:
        channels = {
            row.get("CUST_CHANNEL") for row in rows if row.get("CUST_CHANNEL") is not None
        }
        summary["channels"] = len(channels)
    return summary


def _dim_aliases(dimensions: list[str]) -> list[str]:
    aliases: list[str] = []
    for key in dimensions:
        dim = MKT_DIMENSIONS.get(key)
        if dim is None:
            raise ValueError(f"unknown dimension: {key}")
        aliases.append(dim["alias"])
    return aliases


def _row_key(row: dict[str, Any], aliases: list[str]) -> tuple:
    if not aliases:
        return ()
    return tuple(row.get(alias) for alias in aliases)


def _merge_yoy_rows(
    current_rows: list[dict[str, Any]],
    prior_rows: list[dict[str, Any]],
    aliases: list[str],
) -> list[dict[str, Any]]:
    prior_map = {_row_key(row, aliases): row for row in prior_rows}
    current_keys = {_row_key(row, aliases) for row in current_rows}
    merged: list[dict[str, Any]] = []

    for row in current_rows:
        key = _row_key(row, aliases)
        prior = prior_map.get(key, {})
        current_value = float(row.get("METRIC_VALUE") or 0)
        prior_value = float(prior.get("METRIC_VALUE") or 0)
        delta = round(current_value - prior_value, 2)
        pct = None
        if prior_value != 0:
            pct = round((current_value - prior_value) / prior_value * 100, 2)
        item = {alias: row.get(alias) for alias in aliases}
        item.update(
            {
                "CURRENT_VALUE": round(current_value, 2),
                "PRIOR_VALUE": round(prior_value, 2),
                "DELTA": delta,
                "PCT_CHANGE": pct,
            }
        )
        merged.append(item)

    for row in prior_rows:
        key = _row_key(row, aliases)
        if key in current_keys:
            continue
        prior_value = float(row.get("METRIC_VALUE") or 0)
        item = {alias: row.get(alias) for alias in aliases}
        item.update(
            {
                "CURRENT_VALUE": 0.0,
                "PRIOR_VALUE": round(prior_value, 2),
                "DELTA": round(0.0 - prior_value, 2),
                "PCT_CHANGE": -100.0 if prior_value else None,
            }
        )
        merged.append(item)

    merged.sort(key=lambda r: r.get("CURRENT_VALUE") or 0, reverse=True)
    return merged


def execute_mkt_yoy(request: MktYoyRequest) -> dict[str, Any]:
    as_of = request.as_of or date.today()
    current_from, current_to, prior_from, prior_to = yoy_period_ranges(
        request.mode, as_of
    )
    aliases = _dim_aliases(list(request.dimensions))

    current_req = MktReportRequest(
        dimensions=list(request.dimensions),
        metric=request.metric,
        aggregation=request.aggregation,
        date_from=current_from,
        date_to=current_to,
        channel=request.channel,
        limit=request.limit,
    )
    prior_req = MktReportRequest(
        dimensions=list(request.dimensions),
        metric=request.metric,
        aggregation=request.aggregation,
        date_from=prior_from,
        date_to=prior_to,
        channel=request.channel,
        limit=request.limit,
    )

    current = execute_mkt_report(current_req)
    prior = execute_mkt_report(prior_req)
    rows = _merge_yoy_rows(current["rows"], prior["rows"], aliases)

    current_total = float(current["summary"].get("total") or 0)
    prior_total = float(prior["summary"].get("total") or 0)
    delta = round(current_total - prior_total, 2)
    pct = None
    if prior_total != 0:
        pct = round((current_total - prior_total) / prior_total * 100, 2)

    return {
        "sql": f"-- current\n{current['sql']}\n-- prior\n{prior['sql']}",
        "kind": "yoy",
        "mode": request.mode,
        "as_of": as_of.isoformat(),
        "metric": request.metric,
        "aggregation": request.aggregation,
        "dimensions": list(request.dimensions),
        "current_period": {
            "date_from": current_from.isoformat(),
            "date_to": current_to.isoformat(),
            "total": current_total,
        },
        "prior_period": {
            "date_from": prior_from.isoformat(),
            "date_to": prior_to.isoformat(),
            "total": prior_total,
        },
        "columns": [*aliases, "CURRENT_VALUE", "PRIOR_VALUE", "DELTA", "PCT_CHANGE"],
        "rows": rows,
        "row_count": len(rows),
        "summary": {
            "current_total": current_total,
            "prior_total": prior_total,
            "delta": delta,
            "pct_change": pct,
            "row_count": len(rows),
        },
    }
