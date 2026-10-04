import pytest

from mkt import RETURN_VIEW_NAME, VIEW_NAME
from mkt.chat.sql_guard import SQLPolicyError, validate_and_limit_sql


def test_return_sql_allows_return_view_only():
    sql = validate_and_limit_sql(
        f"SELECT CUST_CHANNEL, SUM(ITEM_AMT1) FROM {RETURN_VIEW_NAME} GROUP BY CUST_CHANNEL",
        view_name=RETURN_VIEW_NAME,
    )
    assert "ROWNUM" in sql


def test_return_sql_rejects_sales_view():
    with pytest.raises(SQLPolicyError):
        validate_and_limit_sql(
            f"SELECT SUM(ITEM_AMT1) FROM {VIEW_NAME}",
            view_name=RETURN_VIEW_NAME,
        )
