import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger("uvicorn.error")


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def identity_sub(identity: dict[str, Any] | None) -> str:
    if not identity:
        return "anonymous"
    return str(
        identity.get("sub")
        or identity.get("preferred_username")
        or identity.get("email")
        or "unknown"
    )


def log_mkt_event(**fields: Any) -> None:
    payload = {key: value for key, value in fields.items() if value is not None}
    logger.info("mkt.audit %s", json.dumps(payload, default=str, ensure_ascii=False))
