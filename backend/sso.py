from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
import os

from dotenv import load_dotenv

load_dotenv()


def resolve_jwks_url() -> str:
    url = (os.getenv("AUTHENTIK_JWKS_URL") or "").strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url

    oidc = (os.getenv("OPENID_PROVIDER_URL") or "").strip()
    suffix = "/.well-known/openid-configuration"
    if oidc.startswith("http") and oidc.endswith(suffix):
        return oidc[: -len(suffix)] + "/jwks/"

    return ""


JWKS_URL = resolve_jwks_url()
SSO_AUDIENCE = os.getenv("OAUTH_CLIENT_ID")
security_scheme = HTTPBearer()
_jwks_client = None


def get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not JWKS_URL:
            raise HTTPException(
                status_code=503,
                detail="AUTHENTIK_JWKS_URL is not configured",
            )
        _jwks_client = PyJWKClient(JWKS_URL)
    return _jwks_client


def verify_sso_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    """
    Function to decode JWT and verify if the token is valid
    """
    token = credentials.credentials
    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=SSO_AUDIENCE,
            options={"verify_aud": True},
        )
        return payload

    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=403, detail="Access Denied: Audience ไม่ถูกต้อง")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token หมดอายุ")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=403, detail=f"Token ไม่ถูกต้อง: {str(e)}")
