import os

import jwt
from fastapi import Depends, FastAPI, HTTPException, APIRouter
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

bearer = HTTPBearer(auto_error=False)

ISSUER = os.environ["AUTHENTIK_ISSUER"]
JWKS_URL = os.environ["AUTHENTIK_JWKS_URL"]
AUDIENCE = os.environ["OAUTH_CLIENT_ID"]

jwks_client = PyJWKClient(JWKS_URL)

def get_current_identity(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bearer token required")

    token = credentials.credentials

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token).key

        return jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require": ["sub", "iss", "aud", "exp"],
            },
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        ) from exc


def require_group(*allowed_groups: str):
    allowed = {
        group.strip().casefold()
        for group in allowed_groups
    }

    def check_permission(
        identity: dict = Depends(get_current_identity),
    ) -> dict:
        token_groups = identity.get("openwebui_groups", [])

        if isinstance(token_groups, str):
            token_groups = [token_groups]

        user_groups = {
            str(group).strip().casefold()
            for group in token_groups
        }

        if not user_groups.intersection(allowed):
            raise HTTPException(
                status_code=403,
                detail="User group is not permitted",
            )

        return identity

    return check_permission


@router.get("/tools/whoami", include_in_schema=True)
def whoami(identity: dict = Depends(get_current_identity)):
    return {
        "sub": identity["sub"],
        "email": identity.get("email"),
        "division": identity.get("division"),
        "department": identity.get("department"),
        "groups": identity.get("openwebui_groups", []),
    }