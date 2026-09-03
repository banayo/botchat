from datetime import timedelta

from export.models import ExportReportRequest
from export.registry import (
    DATE_FILTER_COLUMN,
    EXPORT_DIMENSIONS,
    EXPORT_METRICS,
    FROM_CLAUSE,
)


class QueryBuildError(ValueError):
    pass


def build_export_report_sql(
    request: ExportReportRequest,
) -> tuple[str, dict]:
    metric = EXPORT_METRICS.get(request.metric)
    if metric is None:
        raise QueryBuildError(f"unknown metric: {request.metric}")

    agg_fn = metric["allowed_aggregations"].get(request.aggregation)
    if agg_fn is None:
        raise QueryBuildError(
            f"aggregation {request.aggregation} is not allowed for {request.metric}"
        )

    select_parts: list[str] = []
    group_parts: list[str] = []
    order_parts: list[str] = []
    for key in request.dimensions:
        dim = EXPORT_DIMENSIONS.get(key)
        if dim is None:
            raise QueryBuildError(f"unknown dimension: {key}")
        select_parts.append(f"{dim['expression']} AS {dim['alias']}")
        group_parts.append(dim["expression"])
        order_parts.append(dim["alias"])

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

    if request.country:
        country_dim = EXPORT_DIMENSIONS["country"]
        filter_col = country_dim.get("filter_column", country_dim["expression"])
        where_parts.append(f"{filter_col} = :country")
        params["country"] = request.country

    select_sql = ",\n        ".join(select_parts)
    group_sql = ",\n        ".join(group_parts)
    order_sql = ",\n        ".join(order_parts)
    where_sql = " AND ".join(where_parts)

    inner = f"""SELECT
        {select_sql}
    FROM {FROM_CLAUSE}
    WHERE {where_sql}
    GROUP BY
        {group_sql}
    ORDER BY
        {order_sql}"""

    sql = f"""SELECT *
FROM (
    {inner}
)
WHERE ROWNUM <= :result_limit"""
    return sql, params
