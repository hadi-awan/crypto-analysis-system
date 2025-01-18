import pytest
from datetime import datetime, timedelta
import os
from app.admin.jwt import JWTAuth

# Test setup
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key-123'
    os.environ['JWT_ALGORITHM'] = 'HS256'
    os.environ['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'] = '1440'  # 24 hours
    # Add other required environment variables
    os.environ['API_V1_STR'] = '/api/v1'
    os.environ['PROJECT_NAME'] = 'Test Project'
    os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
    os.environ['BINANCE_API_KEY'] = 'test-key'
    os.environ['BINANCE_SECRET_KEY'] = 'test-secret'
    yield
    # Cleanup
    os.environ.pop('JWT_SECRET_KEY', None)
    os.environ.pop('JWT_ALGORITHM', None)
    os.environ.pop('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', None)

@pytest.fixture
def auth():
    return JWTAuth()

def test_create_token(auth):
    """Test token creation"""
    user_id = 123
    token = auth.create_token(user_id)
    
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_valid_token(auth):
    """Test verification of a valid token"""
    user_id = 123
    token = auth.create_token(user_id)
    
    payload = auth.verify_token(token)
    assert payload is not None
    assert payload['user_id'] == user_id
    assert 'exp' in payload
    assert 'iat' in payload

def test_verify_expired_token(auth):
    """Test verification of an expired token"""
    user_id = 123
    # Create token that expires in -1 seconds
    token = auth.create_token(user_id, expiration=timedelta(seconds=-1))
    
    payload = auth.verify_token(token)
    assert payload is None

def test_verify_invalid_token(auth):
    """Test verification of an invalid token"""
    payload = auth.verify_token("invalid.token.string")
    assert payload is None

def test_different_secret_keys():
    """Test that tokens created with different secret keys are invalid"""
    auth1 = JWTAuth(secret_key="secret1")
    auth2 = JWTAuth(secret_key="secret2")
    
    token = auth1.create_token(123)
    payload = auth2.verify_token(token)
    assert payload is None

def test_token_expiration_time(auth):
    """Test that token expiration time is set correctly"""
    expiration = timedelta(minutes=30)
    token = auth.create_token(123, expiration=expiration)
    payload = auth.verify_token(token)
    
    assert payload is not None
    token_exp = datetime.fromtimestamp(payload['exp'])
    token_iat = datetime.fromtimestamp(payload['iat'])
    actual_expiration = token_exp - token_iat
    
    # Allow 1 second tolerance for test execution time
    assert abs((actual_expiration - expiration).total_seconds()) <= 1

def test_refresh_token(auth):
    """Test refresh token creation and verification"""
    user_id = 123
    refresh_token = auth.create_refresh_token(user_id)
    
    payload = auth.verify_token(refresh_token)
    assert payload is not None
    assert payload['user_id'] == user_id
    
    # Verify it has a longer expiration time
    token_exp = datetime.fromtimestamp(payload['exp'])
    token_iat = datetime.fromtimestamp(payload['iat'])
    expiration = token_exp - token_iat
    
    assert expiration.days >= 7  # Should be at least 7 days