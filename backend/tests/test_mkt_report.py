from datetime import date

import pytest
from pydantic import ValidationError

from mkt.report.models import MktReportRequest, MktYoyRequest
from mkt.report.query_builder import build_mkt_report_sql
from mkt.report.service import _merge_yoy_rows, yoy_period_ranges


def test_same_day_range_allowed():
    req = MktReportRequest(
        dimensions=["channel"],
        metric="sales",
        aggregation="sum",
        date_from=date(2026, 9, 21),
        date_to=date(2026, 9, 21),
    )
    sql, params = build_mkt_report_sql(req)
    assert "SHOP_TYPE" in sql
    assert "CANCEL" not in sql
    assert "METRIC_VALUE DESC" in sql
    assert params["date_from"] == date(2026, 9, 21)
    assert params["date_to"] == date(2026, 9, 22)


def test_total_without_dimensions():
    req = MktReportRequest(
        dimensions=[],
        metric="quantity",
        aggregation="sum",
        date_from=date(2026, 9, 1),
        date_to=date(2026, 9, 22),
    )
    sql, _params = build_mkt_report_sql(req)
    assert "GROUP BY" not in sql
    assert "SUM(" in sql
    assert "QTY1" in sql


def test_dept_dimension_uses_cust_channel():
    req = MktReportRequest(
        dimensions=["dept"],
        metric="sales",
        aggregation="sum",
        date_from=date(2026, 9, 21),
        date_to=date(2026, 9, 21),
    )
    sql, _params = build_mkt_report_sql(req)
    assert "CUST_CHANNEL" in sql
    assert "GROUP BY" in sql
    assert "CUST_CHANNEL" in sql.split("GROUP BY", 1)[1]


def test_channel_filter_bind():
    req = MktReportRequest(
        dimensions=["channel"],
        metric="sales",
        aggregation="sum",
        date_from=date(2026, 9, 1),
        date_to=date(2026, 9, 22),
        channel="ONLINE",
    )
    sql, params = build_mkt_report_sql(req)
    assert "SHOP_TYPE = :channel" in sql
    assert params["channel"] == "ONLINE"


def test_dept_filter_bind():
    req = MktReportRequest(
        dimensions=["dept"],
        metric="sales",
        aggregation="sum",
        date_from=date(2026, 9, 1),
        date_to=date(2026, 9, 22),
        dept="ONL",
    )
    sql, params = build_mkt_report_sql(req)
    assert "CUST_CHANNEL = :dept" in sql
    assert params["dept"] == "ONL"


def test_date_to_before_from_rejected():
    with pytest.raises(ValidationError):
        MktReportRequest(
            dimensions=["channel"],
            metric="sales",
            aggregation="sum",
            date_from=date(2026, 9, 22),
            date_to=date(2026, 9, 21),
        )


def test_mtd_yoy_ranges():
    current_from, current_to, prior_from, prior_to = yoy_period_ranges(
        "mtd_yoy", date(2026, 9, 22)
    )
    assert current_from == date(2026, 9, 1)
    assert current_to == date(2026, 9, 22)
    assert prior_from == date(2025, 9, 1)
    assert prior_to == date(2025, 9, 22)


def test_full_month_yoy_ranges():
    current_from, current_to, prior_from, prior_to = yoy_period_ranges(
        "full_month_yoy", date(2026, 9, 22)
    )
    assert current_from == date(2026, 9, 1)
    assert current_to == date(2026, 9, 30)
    assert prior_from == date(2025, 9, 1)
    assert prior_to == date(2025, 9, 30)


def test_yoy_rejects_month_dimension():
    with pytest.raises(ValidationError):
        MktYoyRequest(dimensions=["month"], mode="mtd_yoy")


def test_merge_yoy_rows():
    current = [
        {"SHOP_TYPE": "A", "METRIC_VALUE": 120},
        {"SHOP_TYPE": "B", "METRIC_VALUE": 80},
    ]
    prior = [
        {"SHOP_TYPE": "A", "METRIC_VALUE": 100},
        {"SHOP_TYPE": "C", "METRIC_VALUE": 50},
    ]
    merged = _merge_yoy_rows(current, prior, ["SHOP_TYPE"])
    by_ch = {row["SHOP_TYPE"]: row for row in merged}
    assert by_ch["A"]["DELTA"] == 20
    assert by_ch["A"]["PCT_CHANGE"] == 20.0
    assert by_ch["B"]["PRIOR_VALUE"] == 0.0
    assert by_ch["C"]["CURRENT_VALUE"] == 0.0
    assert by_ch["C"]["PCT_CHANGE"] == -100.0
