from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Supports .env files for local development and env vars for production/cloud.
    """
    MONGODB_URI: str
    API_TOKEN: Optional[str] = None
    QDRANT_URL: str
    LANGSMITH_API_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = "eu-entral-1"
    AWS_SECRET_NAME: Optional[str] = None
    PROMETHEUS_PUSHGATEWAY_URL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Usage example:
# from src.config.settings import Settings
# settings = Settings()
# print(settings.MONGODB_URI)

settings = Settings() 