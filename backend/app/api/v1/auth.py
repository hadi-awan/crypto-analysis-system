from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.admin.jwt import jwt
from typing import Optional
from app.core.config import get_settings


security = HTTPBearer()

# Ensure get_settings() is correctly used to retrieve environment variables
async def verify_token(credentials: HTTPAuthorizationCredentials):
    settings = get_settings()  # Access settings explicitly here
    secret_key = settings.JWT_SECRET_KEY

    # Example of decoding the JWT (this is where the token is verified)
    try:
        payload = jwt.decode(credentials.credentials, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")