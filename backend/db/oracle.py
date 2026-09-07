import logging
from functools import lru_cache
from typing import Literal

import oracledb
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from database import get_export_oracle_uri, get_mkt_oracle_uri

logger = logging.getLogger("uvicorn.error")

QUERY_TIMEOUT_MS = 60_000
OracleRole = Literal["export", "mkt"]


def _make_engine(uri: str) -> Engine:
    common = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 5,
        "max_overflow": 5,
    }
    try:
        return create_engine(
            uri,
            enable_offset_fetch=False,
            max_identifier_length=30,
            **common,
        )
    except TypeError:
        return create_engine(uri, **common)


@lru_cache(maxsize=2)
def get_oracle_engine(role: OracleRole = "export") -> Engine:
    if oracledb.is_thin_mode():
        logger.warning(
            "oracledb is in thin mode; Oracle 11g typically needs Instant Client (thick mode)"
        )
    else:
        logger.info("oracledb thick mode is active")

    uri = get_export_oracle_uri() if role == "export" else get_mkt_oracle_uri()
    logger.info("oracle engine role=%s", role)
    return _make_engine(uri)
