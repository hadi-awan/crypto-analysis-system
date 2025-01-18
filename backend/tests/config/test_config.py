import pytest
from app.config.config import Settings
from pydantic import AnyHttpUrl, ValidationError

def test_settings_with_env_vars(monkeypatch):
    """Test settings with environment variables"""
    # Setup test environment variables
    test_env = {
        "API_V1_STR": "/api/v1",
        "PROJECT_NAME": "TestProject",
        "BACKEND_CORS_ORIGINS": '["http://localhost:3000"]',
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "BINANCE_API_KEY": "test_key",
        "BINANCE_SECRET_KEY": "test_secret",
        "JWT_SECRET_KEY": "test-jwt-secret",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "1440"  # String value
    }
    
    # Set environment variables
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    # Get settings instance
    settings = Settings(_env_file=None)  # Disable .env file reading for test
    
    # Verify settings
    assert settings.PROJECT_NAME == "TestProject"
    assert settings.API_V1_STR == "/api/v1"
    assert str(settings.BACKEND_CORS_ORIGINS[0]) == "http://localhost:3000/"
    assert settings.DATABASE_URL == "postgresql://test:test@localhost:5432/test"
    assert settings.BINANCE_API_KEY == "test_key"
    assert settings.JWT_SECRET_KEY == "test-jwt-secret"
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 1440  # Should be converted to int

def test_settings_with_direct_values():
    """Test settings with direct values"""
    settings = Settings(
        API_V1_STR="/api/v1",
        PROJECT_NAME="TestProject",
        BACKEND_CORS_ORIGINS=[AnyHttpUrl("http://localhost:3000")],
        DATABASE_URL="postgresql://test:test@localhost:5432/test",
        BINANCE_API_KEY="test_key",
        BINANCE_SECRET_KEY="test_secret",
        JWT_SECRET_KEY="test-jwt-secret",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440,  # Integer value
        _env_file=None
    )
    assert settings.PROJECT_NAME == "TestProject"
    assert str(settings.BACKEND_CORS_ORIGINS[0]) == "http://localhost:3000/"
    assert settings.JWT_SECRET_KEY == "test-jwt-secret"
    assert settings.JWT_ALGORITHM == "HS256"  # Should use default value
    assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 1440

def test_missing_required_settings():
    """Test that missing required fields raise an error"""
    with pytest.raises(ValidationError):
        Settings(API_V1_STR="/api/v1", _env_file=None)  # Missing other required fields

def test_jwt_settings_validation():
    """Test JWT specific settings validation"""
    # Test with invalid algorithm
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            API_V1_STR="/api/v1",
            PROJECT_NAME="TestProject",
            BACKEND_CORS_ORIGINS=[AnyHttpUrl("http://localhost:3000")],
            DATABASE_URL="postgresql://test:test@localhost:5432/test",
            BINANCE_API_KEY="test_key",
            BINANCE_SECRET_KEY="test_secret",
            JWT_SECRET_KEY="test-secret",
            JWT_ALGORITHM="INVALID",  # Invalid algorithm
            _env_file=None
        )
    assert "JWT_ALGORITHM" in str(exc_info.value)

    # Test with invalid token expiration
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            API_V1_STR="/api/v1",
            PROJECT_NAME="TestProject",
            BACKEND_CORS_ORIGINS=[AnyHttpUrl("http://localhost:3000")],
            DATABASE_URL="postgresql://test:test@localhost:5432/test",
            BINANCE_API_KEY="test_key",
            BINANCE_SECRET_KEY="test_secret",
            JWT_SECRET_KEY="test-secret",
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES=-1,  # Invalid expiration
            _env_file=None
        )
    assert "JWT_ACCESS_TOKEN_EXPIRE_MINUTES" in str(exc_info.value)

    # Test with non-numeric expiration string
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            API_V1_STR="/api/v1",
            PROJECT_NAME="TestProject",
            BACKEND_CORS_ORIGINS=[AnyHttpUrl("http://localhost:3000")],
            DATABASE_URL="postgresql://test:test@localhost:5432/test",
            BINANCE_API_KEY="test_key",
            BINANCE_SECRET_KEY="test_secret",
            JWT_SECRET_KEY="test-secret",
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES="invalid",  # Non-numeric string
            _env_file=None
        )
    assert "JWT_ACCESS_TOKEN_EXPIRE_MINUTES" in str(exc_info.value)