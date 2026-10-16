from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AlertEvent(StrEnum):
    INCIDENT_OPENED = "incident_opened"
    INCIDENT_CLOSED = "incident_closed"


@dataclass(frozen=True)
class AlertContext:
    event: AlertEvent
    monitor_name: str
    monitor_url: str
    incident_started_at: datetime
    incident_resolved_at: datetime | None
