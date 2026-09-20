import os
import urllib.parse
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import oracledb

load_dotenv()


def _init_oracle_thick_mode():
    lib_dir = os.getenv("ORACLE_CLIENT_LIB_DIR")
    kwargs = {}
    if lib_dir:
        kwargs["lib_dir"] = lib_dir
    try:
        oracledb.init_oracle_client(**kwargs)
    except Exception:
        # already initialized, or Instant Client missing on this machine
        pass


_init_oracle_thick_mode()


def get_oracle_langchain_db_uri(user: str | None = None, password: str | None = None):
    oracle_user = user if user is not None else os.getenv("ORACLE_USER")
    oracle_password = urllib.parse.quote_plus(
        password if password is not None else os.getenv("ORACLE_PASSWORD", "")
    )
    oracle_host = os.getenv("ORACLE_HOST")
    oracle_port = os.getenv("ORACLE_PORT", "1521")
    oracle_service = os.getenv("ORACLE_SERVICE")
    return (
        f"oracle+oracledb://{oracle_user}:{oracle_password}"
        f"@{oracle_host}:{oracle_port}/?service_name={oracle_service}"
    )


def get_export_oracle_uri():
    user = os.getenv("EXPORT_ORACLE_USER")
    if user:
        return get_oracle_langchain_db_uri(user, os.getenv("EXPORT_ORACLE_PASSWORD", ""))
    return get_oracle_langchain_db_uri()


def get_mkt_oracle_uri():
    user = os.getenv("MKT_ORACLE_USER")
    if user:
        return get_oracle_langchain_db_uri(user, os.getenv("MKT_ORACLE_PASSWORD", ""))
    return get_oracle_langchain_db_uri()


def get_sales_langchain_db_uri():
    db_user = os.getenv("SALES_DB_USER")
    db_password = os.getenv("SALES_DB_PASSWORD")
    db_host = os.getenv("SALES_DB_HOST")
    db_port = os.getenv("SALES_DB_PORT")
    db_name = os.getenv("SALES_DB_NAME")

    return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
