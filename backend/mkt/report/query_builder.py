from datetime import timedelta

from mkt.report.models import MktReportRequest
from mkt.report.registry import (
    DATE_FILTER_COLUMN,
    MKT_DIMENSIONS,
    MKT_METRICS,
    FROM_CLAUSE,
    REGISTRY_READY,
)


class QueryBuildError(ValueError):
    pass


# Every name the registry uses for a dimension (key, alias, column, expression).
# None of these is ever a real filter value; seeing one means the LLM meant
# "group by" - e.g. channel="SHOP_TYPE" -> WHERE SHOP_TYPE = 'SHOP_TYPE' -> 0 rows.
_DIMENSION_NAMES = frozenset(
    str(name).upper()
    for key, dim in MKT_DIMENSIONS.items()
    for name in (key, dim.get("alias"), dim.get("expression"), dim.get("filter_column"))
    if name
)


def _add_filter(key: str, value: str | None, where_parts: list[str], params: dict) -> None:
    value = (value or "").strip()
    if not value:
        return
    dim = MKT_DIMENSIONS.get(key)
    if dim is None:
        raise QueryBuildError(f"{key} dimension is not configured")
    if value.upper() in _DIMENSION_NAMES:
        raise QueryBuildError(
            f"{key}={value!r} is a column name, not a {key} value. "
            f"To break down by {key}, use dimensions=['{key}'] and leave {key} empty."
        )
    if dim.get("filter_case") == "upper":
        value = value.upper()  # exact match; "Online" would otherwise find 0 rows
    filter_col = dim.get("filter_column", dim["expression"])
    where_parts.append(f"{filter_col} = :{key}")
    params[key] = value


def build_mkt_report_sql(request: MktReportRequest) -> tuple[str, dict]:
    if not REGISTRY_READY:
        raise QueryBuildError(
            "marketing report registry is not configured; run sql/collect_mkt_view.sql first"
        )
    if not DATE_FILTER_COLUMN:
        raise QueryBuildError("DATE_FILTER_COLUMN is not configured")

    metric = MKT_METRICS.get(request.metric)
    if metric is None:
        raise QueryBuildError(f"unknown metric: {request.metric}")

    agg_fn = metric["allowed_aggregations"].get(request.aggregation)
    if agg_fn is None:
        raise QueryBuildError(
            f"aggregation {request.aggregation} is not allowed for {request.metric}"
        )

    select_parts: list[str] = []
    group_parts: list[str] = []
    for key in request.dimensions:
        dim = MKT_DIMENSIONS.get(key)
        if dim is None:
            raise QueryBuildError(f"unknown dimension: {key}")
        select_parts.append(f"{dim['expression']} AS {dim['alias']}")
        group_parts.append(dim["expression"])

    expr = metric["base_expression"].strip()
    select_parts.append(f"{agg_fn}(\n            {expr}\n        ) AS METRIC_VALUE")

    where_parts = [
        f"{DATE_FILTER_COLUMN} >= :date_from",
        f"{DATE_FILTER_COLUMN} < :date_to",
        *metric.get("mandatory_filters", []),
    ]
    params: dict = {
        "date_from": request.date_from,
        "date_to": request.date_to + timedelta(days=1),
        "result_limit": request.limit,
    }

    _add_filter("channel", request.channel, where_parts, params)
    _add_filter("dept", request.dept, where_parts, params)

    select_sql = ",\n        ".join(select_parts)
    where_sql = " AND ".join(where_parts)

    if group_parts:
        group_sql = ",\n        ".join(group_parts)
        group_clause = f"""
    GROUP BY
        {group_sql}"""
    else:
        group_clause = ""

    inner = f"""SELECT
        {select_sql}
    FROM {FROM_CLAUSE}
    WHERE {where_sql}{group_clause}
    ORDER BY
        METRIC_VALUE DESC NULLS LAST"""

    sql = f"""SELECT *
FROM (
    {inner}
)
WHERE ROWNUM <= :result_limit"""
    return sql, params
