import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.api.v1.auth import verify_token
from app.admin.jwt import JWTAuth  # Import from shared code
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def valid_token():
    auth = JWTAuth()
    return auth.create_token(user_id=123)

@pytest.fixture
def expired_token():
    auth = JWTAuth()
    return auth.create_token(user_id=123, expiration=timedelta(seconds=-1))

@pytest.mark.asyncio
async def test_valid_token_verification(valid_token):
    """Test verification of a valid token"""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_token)
    payload = await verify_token(credentials)
    
    assert payload is not None
    assert payload['user_id'] == 123

@pytest.mark.asyncio
async def test_expired_token_verification(expired_token):
    """Test verification of an expired token"""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)
    
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(credentials)
    
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_invalid_token_verification():
    """Test verification of an invalid token"""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")
    
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(credentials)
    
    assert exc_info.value.status_code == 401