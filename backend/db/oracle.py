import logging
from functools import lru_cache

import oracledb
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from database import get_oracle_langchain_db_uri

logger = logging.getLogger("uvicorn.error")

QUERY_TIMEOUT_MS = 60_000


@lru_cache(maxsize=1)
def get_oracle_engine() -> Engine:
    if oracledb.is_thin_mode():
        logger.warning(
            "oracledb is in thin mode; Oracle 11g typically needs Instant Client (thick mode)"
        )
    else:
        logger.info("oracledb thick mode is active")

    uri = get_oracle_langchain_db_uri()
    common = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 5,
        "max_overflow": 5,
        # "connect_args": {"call_timeout": QUERY_TIMEOUT_MS},
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
