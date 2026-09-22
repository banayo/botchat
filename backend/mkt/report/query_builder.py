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

    if request.channel:
        channel_dim = MKT_DIMENSIONS.get("channel")
        if channel_dim is None:
            raise QueryBuildError("channel dimension is not configured")
        filter_col = channel_dim.get("filter_column", channel_dim["expression"])
        where_parts.append(f"{filter_col} = :channel")
        params["channel"] = request.channel

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
