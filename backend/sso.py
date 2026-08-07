from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from typing import List
import os

JWKS_URL = os.getenv("AUTHENTIK_JWKS_URL")
SSO_AUDIENCE = os.getenv("OAUTH_CLIENT_ID")

jwks_client = PyJWKClient(JWKS_URL)
security_scheme = HTTPBearer()

def verify_sso_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    """
    Function to decode JWT and verify if the token is valid
    """
    token = credentials.credentials
    try:
        # Get Signing Key (Public Key) from SSO
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and verify the token
        payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=SSO_AUDIENCE,  
                options={"verify_aud": True} 
            )
            
        # If the token is decoded successfully, return the payload
        return payload
        
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=403, detail="Access Denied: Audience ไม่ถูกต้อง")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token หมดอายุ")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=403, detail=f"Token ไม่ถูกต้อง: {str(e)}")