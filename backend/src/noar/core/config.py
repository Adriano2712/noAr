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
    access_token_expire_minutes: int = 60 * 24
    # Comma-separated: the Next.js dev server (docker-compose) and the port
    # Playwright's own production-build server uses for e2e (see
    # web/playwright.config.ts) are different origins in the browser's eyes.
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:3100"

    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    smtp_from: str = "noar@localhost"

    telegram_bot_token: str = ""
    telegram_api_base_url: str = "https://api.telegram.org"

    webhook_receiver_url: str = "http://webhook-receiver:8080"
    demo_target_url: str = "http://demo-target:80"

    scheduler_batch_size: int = 20
    scheduler_lease_seconds: int = 60
    scheduler_poll_interval_seconds: float = 5.0
    scheduler_jitter_fraction: float = 0.1
    scheduler_check_concurrency: int = 10

    # Off by default (blocks private/loopback/link-local targets); the local
    # Docker Compose demo turns this on so the worker can reach demo-target.
    ssrf_allow_private_networks: bool = False

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
