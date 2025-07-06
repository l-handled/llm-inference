from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class AppConfig(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """
    api_token: str = Field(..., env="API_TOKEN")
    qdrant_host: str = Field("localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(6333, env="QDRANT_PORT")
    environment: Optional[str] = Field("local", env="ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8" 