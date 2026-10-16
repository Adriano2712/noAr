from datetime import UTC, datetime

from noar.alerts.events import AlertContext, AlertEvent
from noar.core.config import Settings

TEST_DATABASE_URL = "postgresql+asyncpg://noar:noar_dev_password@localhost:5432/noar"


def make_settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "database_url": TEST_DATABASE_URL,
        "api_secret_key": "test-secret-key-at-least-32-bytes-long",
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def make_context(event: AlertEvent = AlertEvent.INCIDENT_OPENED) -> AlertContext:
    return AlertContext(
        event=event,
        monitor_name="Example",
        monitor_url="https://example.com",
        incident_started_at=datetime(2026, 1, 1, tzinfo=UTC),
        incident_resolved_at=datetime(2026, 1, 1, 0, 10, tzinfo=UTC)
        if event is AlertEvent.INCIDENT_CLOSED
        else None,
    )
