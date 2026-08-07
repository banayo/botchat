import logging
import os
from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
    PyJWKClientConnectionError,
    PyJWKClientError,
)

from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)

AUTHENTIK_ISSUER = os.getenv("AUTHENTIK_ISSUER")
AUTHENTIK_JWKS_URL = os.getenv("AUTHENTIK_JWKS_URL")
AUTHENTIK_AUDIENCE = os.getenv("AUTHENTIK_AUDIENCE")

AUTHENTIK_GROUP_CLAIM = os.getenv(
    "AUTHENTIK_GROUP_CLAIM",
    "openwebui_groups",
)

ALLOWED_ALGORITHMS = ["RS256"]

jwks_client = PyJWKClient(
    AUTHENTIK_JWKS_URL,
    cache_jwk_set=True,
    lifespan=300,
    timeout=10,
    headers={
        "Accept": "application/json",
        "User-Agent": "inventory-api-jwks/1.0",
    },
)


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_identity(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict[str, Any]:

    if credentials is None:
        raise unauthorized("Bearer access token required")

    if credentials.scheme.casefold() != "bearer":
        raise unauthorized("Bearer authentication required")

    token = credentials.credentials
    
    logger = logging.getLogger("uvicorn.error")

    debug_claims = jwt.decode(
        token,
        options={
            "verify_signature": False,
            "verify_exp": False,
            "verify_aud": False,
            "verify_iss": False,
        },
    )

    logger.warning(
        "JWT received aud=%r, expected aud=%r, iss=%r",
        debug_claims.get("aud"),
        AUTHENTIK_AUDIENCE,
        debug_claims.get("iss"),
    )

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

    except PyJWKClientConnectionError as exc:
        logger.error("Unable to reach Authentik JWKS endpoint")
        raise HTTPException(
            status_code=503,
            detail="Identity verification service unavailable",
        ) from exc

    except (PyJWKClientError, InvalidTokenError) as exc:
        logger.warning(
            "Unable to resolve JWT signing key: %s",
            type(exc).__name__,
        )
        raise unauthorized("Invalid access token") from exc

    try:
        identity = jwt.decode(
            token,
            key=signing_key.key,
            algorithms=ALLOWED_ALGORITHMS,
            issuer=AUTHENTIK_ISSUER,
            audience=AUTHENTIK_AUDIENCE,
            leeway=30,
            options={
                "require": [
                    "sub",
                    "iss",
                    "aud",
                    "exp",
                ],
            },
        )

    except ExpiredSignatureError as exc:
        raise unauthorized("Access token expired") from exc

    except InvalidAudienceError as exc:
        raise unauthorized("Invalid access token audience") from exc

    except InvalidIssuerError as exc:
        raise unauthorized("Invalid access token issuer") from exc

    except InvalidTokenError as exc:
        logger.warning(
            "JWT validation failed: %s",
            type(exc).__name__,
        )
        raise unauthorized("Invalid access token") from exc

    return identity


def normalize_claim_values(value: Any) -> set[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        return set()

    return {
        item.strip().casefold()
        for item in values
        if isinstance(item, str) and item.strip()
    }


def require_group(*allowed_groups: str):
    allowed = {
        group.strip().casefold()
        for group in allowed_groups
        if group.strip()
    }

    if not allowed:
        raise ValueError("At least one allowed group is required")

    def check_permission(
        identity: dict[str, Any] = Depends(get_current_identity),
    ) -> dict[str, Any]:
        user_groups = normalize_claim_values(
            identity.get(AUTHENTIK_GROUP_CLAIM)
        )

        if not user_groups.intersection(allowed):
            raise HTTPException(
                status_code=403,
                detail="User group is not permitted",
            )

        return identity

    return check_permission


@router.get("/whoami")
def whoami(
    identity: dict[str, Any] = Depends(get_current_identity),
):
    return {
        "sub": identity["sub"],
        "issuer": identity["iss"],
        "audience": identity["aud"],
        "email": identity.get("email"),
        "division": identity.get("division"),
        "department": identity.get("department"),
        "roles": identity.get("roles", []),
        "groups": identity.get(AUTHENTIK_GROUP_CLAIM, []),
        "scope": identity.get("scope"),
    }