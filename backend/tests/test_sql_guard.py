import pytest

from export.sql_guard import SQLPolicyError, validate_and_limit_sql


def test_select_from_view_is_wrapped_with_rownum():
    sql = validate_and_limit_sql(
        "SELECT ZONE_NAME FROM KMPROD.EXP$ERP_SALE_REP_EXP WHERE CANCEL = 'N'"
    )
    assert "ROWNUM <= 50" in sql
    assert sql.strip().startswith("SELECT * FROM")


def test_rejects_dml():
    with pytest.raises(SQLPolicyError):
        validate_and_limit_sql("DELETE FROM KMPROD.EXP$ERP_SALE_REP_EXP")


def test_rejects_other_table():
    with pytest.raises(SQLPolicyError):
        validate_and_limit_sql("SELECT * FROM DBA_USERS")


def test_rejects_database_link():
    with pytest.raises(SQLPolicyError):
        validate_and_limit_sql(
            "SELECT * FROM KMPROD.EXP$ERP_SALE_REP_EXP@REMOTE"
        )


def test_rejects_multiple_statements():
    with pytest.raises(SQLPolicyError):
        validate_and_limit_sql(
            "SELECT * FROM KMPROD.EXP$ERP_SALE_REP_EXP; DROP TABLE X"
        )


def test_rejects_fetch_first():
    with pytest.raises(SQLPolicyError):
        validate_and_limit_sql(
            "SELECT * FROM KMPROD.EXP$ERP_SALE_REP_EXP FETCH FIRST 10 ROWS ONLY"
        )


def test_strips_trailing_semicolon():
    sql = validate_and_limit_sql("SELECT * FROM exp$erp_sale_rep_exp;")
    inner = sql.split(") WHERE ROWNUM")[0]
    assert "exp$erp_sale_rep_exp" in inner.lower()
    assert not inner.strip().endswith(";")
