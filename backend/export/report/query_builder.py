from datetime import timedelta

from export.report.models import ExportReportRequest
from export.report.registry import (
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
    metric = EXPORT_METRICS.get(request.metric)# ส่ง ค่า metric ไปยัง registry.py
    if metric is None:
        raise QueryBuildError(f"unknown metric: {request.metric}")

    agg_fn = metric["allowed_aggregations"].get(request.aggregation)# SUM หรือ AVG
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
        select_parts.append(f"{dim['expression']} AS {dim['alias']}")# SELECT CRETRUNC(CRE_DATE, 'MM')_DATE AS MONTH_KEY
        group_parts.append(dim["expression"])# GROUP BY CRE_DATE ดึงจาก ชื่อเล่นไม่ได้
        order_parts.append(dim["alias"])#order by MONTH_KEY ดึงจาก ชื่อเล่นได้

    expr = metric["base_expression"].strip()# CASE WHEN MODULE IN ('RT', 'CN', 'IV', 'DN') THEN ITEM_AMT1 ELSE 0 END
    select_parts.append(f"{agg_fn}(\n            {expr}\n        ) AS METRIC_VALUE")# SUM(CASE WHEN MODULE IN ('RT', 'CN', 'IV', 'DN') THEN ITEM_AMT1 ELSE 0 END) AS METRIC_VALUE
    # select_parts=SELECT CRETRUNC(CRE_DATE, 'MM')_DATE AS MONTH_KEY
    #               SUM(CASE WHEN MODULE IN ('RT', 'CN', 'IV', 'DN') THEN ITEM_AMT1 ELSE 0 END) AS METRIC_VALUE
    where_parts = [
        f"{DATE_FILTER_COLUMN} >= :date_from",# CRE_DATE >= :date_from
        f"{DATE_FILTER_COLUMN} < :date_to",# CRE_DATE < :date_to
        *metric.get("mandatory_filters", []),# CANCEL = 'N'
    ]
    params: dict = {
        "date_from": request.date_from,# 2025-01-01
        "date_to": request.date_to + timedelta(days=1),# 2025-12-31 + 1 = 2026-01-01
        "result_limit": request.limit,# 500
    }

    if request.country:# ถ้ามีค่า country จะเพิ่มค่า country ไปยัง where_parts
        country_dim = EXPORT_DIMENSIONS["country"]
        filter_col = country_dim.get("filter_column", country_dim["expression"])
        where_parts.append(f"{filter_col} = :country")
        params["country"] = request.country

    select_sql = ",\n        ".join(select_parts)# SELECT CRETRUNC(CRE_DATE, 'MM')_DATE AS MONTH_KEY, SUM(CASE WHEN MODULE IN ('RT', 'CN', 'IV', 'DN') THEN ITEM_AMT1 ELSE 0 END) AS METRIC_VALUE
    group_sql = ",\n        ".join(group_parts)# GROUP BY CRE_DATE
    order_sql = ",\n        ".join(order_parts)# ORDER BY MONTH_KEY
    where_sql = " AND ".join(where_parts)# CRE_DATE >= :date_from AND CRE_DATE < :date_to AND CANCEL = 'N'

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
# ผล
# SELECT *
# FROM (
#     SELECT
#         TRUNC(CRE_DATE, 'MM') AS MONTH_KEY,
#         ZONE_NAME AS COUNTRY,
#         SUM( CASE WHEN MODULE IN ('RT', 'CN', 'IV', 'DN') THEN ITEM_AMT1 ELSE 0 END ) AS METRIC_VALUE
#     FROM KMPROD.EXP$ERP_SALE_REP_EXP
#     WHERE CRE_DATE >= :date_from
#       AND CRE_DATE < :date_to
#       AND CANCEL = 'N'
#     GROUP BY
#         TRUNC(CRE_DATE, 'MM'),
#         ZONE_NAME
#     ORDER BY
#         MONTH_KEY,
#         COUNTRY
# )
# WHERE ROWNUM <= :result_limit