import os
from typing import Any

from fastapi import Depends, HTTPException

from routers.auth import (
    AUTHENTIK_GROUP_CLAIM,
    get_current_identity,
    normalize_claim_values,
)


def require_export_access(
    identity: dict[str, Any] = Depends(get_current_identity),
) -> dict[str, Any]:
    raw = (os.getenv("EXPORT_ALLOWED_GROUPS") or "").strip()
    if not raw:
        return identity

    allowed = {item.strip().casefold() for item in raw.split(",") if item.strip()}
    user_groups = normalize_claim_values(identity.get(AUTHENTIK_GROUP_CLAIM))
    if not user_groups.intersection(allowed):
        raise HTTPException(status_code=403, detail="User group is not permitted")
    return identity
