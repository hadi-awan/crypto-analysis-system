from typing import List
from functools import lru_cache
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

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