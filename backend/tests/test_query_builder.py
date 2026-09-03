from datetime import date

from export.models import ExportReportRequest
from export.query_builder import build_export_report_sql


def test_controlled_sql_uses_registry_columns_and_bind_params():
    request = ExportReportRequest(
        dimensions=["month", "country"],
        metric="sales",
        aggregation="sum",
        date_from=date(2024, 1, 1),
        date_to=date(2024, 12, 31),
        country="JP",
        limit=100,
    )
    sql, params = build_export_report_sql(request)
    assert "KMPROD.EXP$ERP_SALE_REP_EXP" in sql
    assert "TRUNC(CRE_DATE, 'MM')" in sql
    assert "ZONE_NAME" in sql
    assert "CANCEL = 'N'" in sql
    assert "FETCH FIRST" not in sql.upper()
    assert "ROWNUM <= :result_limit" in sql
    assert params["date_from"] == date(2024, 1, 1)
    assert params["date_to"].isoformat() == "2025-01-01"
    assert params["country"] == "JP"
    assert params["result_limit"] == 100
    assert ":date_from" in sql
    assert "ITEM_AMT1" in sql
    assert "-ITEM_AMT1" in sql


def test_quantity_uses_qty1():
    request = ExportReportRequest(
        dimensions=["country"],
        metric="quantity",
        aggregation="sum",
        date_from=date(2024, 1, 1),
        date_to=date(2024, 1, 31),
    )
    sql, _params = build_export_report_sql(request)
    assert "QTY1" in sql
    assert "ITEM_AMT1" not in sql
