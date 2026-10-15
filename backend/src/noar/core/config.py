from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    database_url: PostgresDsn

    api_secret_key: str
    api_port: int = 8000

    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    smtp_from: str = "noar@localhost"

    telegram_bot_token: str = ""
    telegram_api_base_url: str = "https://api.telegram.org"

    webhook_receiver_url: str = "http://webhook-receiver:8080"
    demo_target_url: str = "http://demo-target:80"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
