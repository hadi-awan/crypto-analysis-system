from typing import List, Union
from functools import lru_cache
from pydantic import AnyHttpUrl, Field, BeforeValidator
from typing_extensions import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

VALID_JWT_ALGORITHMS = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]

def validate_jwt_algorithm(v: str) -> str:
    if v not in VALID_JWT_ALGORITHMS:
        raise ValueError(f"JWT_ALGORITHM must be one of {VALID_JWT_ALGORITHMS}")
    return v

def validate_jwt_expire_minutes(v: Union[str, int]) -> int:
    # Convert string to int if necessary
    if isinstance(v, str):
        try:
            v = int(v)
        except ValueError:
            raise ValueError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be a valid integer")
    
    if v <= 0:
        raise ValueError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
    return v

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str
    PROJECT_NAME: str

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database Settings
    DATABASE_URL: str

    # Exchange API Settings
    BINANCE_API_KEY: str
    BINANCE_SECRET_KEY: str

    # JWT Settings
    JWT_SECRET_KEY: str = Field(..., description="Secret key for JWT token generation")
    JWT_ALGORITHM: Annotated[str, BeforeValidator(validate_jwt_algorithm)] = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Annotated[int, BeforeValidator(validate_jwt_expire_minutes)] = 60 * 24

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

    @classmethod
    def parse_env_var(cls, field_name: str, raw_val: str) -> any:
        if field_name == "BACKEND_CORS_ORIGINS":
            return json.loads(raw_val)
        return raw_val

@lru_cache()
def get_settings() -> Settings:
    return Settings()