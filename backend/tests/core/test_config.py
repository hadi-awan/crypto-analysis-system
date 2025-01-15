import pytest
from app.core.config import Settings
from pydantic import AnyHttpUrl

def test_settings_with_env_vars(monkeypatch):
    """Test settings with environment variables"""
    # Setup test environment variables
    test_env = {
        "API_V1_STR": "/api/v1",
        "PROJECT_NAME": "TestProject",
        "BACKEND_CORS_ORIGINS": '["http://localhost:3000"]',
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "BINANCE_API_KEY": "test_key",
        "BINANCE_SECRET_KEY": "test_secret"
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

def test_settings_with_direct_values():
    """Test settings with direct values"""
    settings = Settings(
        API_V1_STR="/api/v1",
        PROJECT_NAME="TestProject",
        BACKEND_CORS_ORIGINS=[AnyHttpUrl("http://localhost:3000")],
        DATABASE_URL="postgresql://test:test@localhost:5432/test",
        BINANCE_API_KEY="test_key",
        BINANCE_SECRET_KEY="test_secret",
        _env_file=None  # Disable .env file reading for test
    )
    assert settings.PROJECT_NAME == "TestProject"
    assert str(settings.BACKEND_CORS_ORIGINS[0]) == "http://localhost:3000/"

def test_missing_required_settings():
    """Test that missing required fields raise an error"""
    with pytest.raises(Exception):
        Settings(API_V1_STR="/api/v1", _env_file=None)  # Missing other required fields