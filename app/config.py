from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./cloudops.db"
    ai_provider: str = "mock"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = ""
    bedrock_knowledge_base_id: str = ""
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

