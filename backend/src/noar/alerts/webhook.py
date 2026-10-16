import httpx

from noar.alerts.events import AlertContext
from noar.core.config import Settings
from noar.security.ssrf import ensure_safe_url


async def send_webhook_alert(
    webhook_url: str, context: AlertContext, settings: Settings, client: httpx.AsyncClient
) -> None:
    await ensure_safe_url(webhook_url, allow_private=settings.ssrf_allow_private_networks)

    payload = {
        "event": context.event.value,
        "monitor_name": context.monitor_name,
        "monitor_url": context.monitor_url,
        "incident_started_at": context.incident_started_at.isoformat(),
        "incident_resolved_at": (
            context.incident_resolved_at.isoformat() if context.incident_resolved_at else None
        ),
    }
    response = await client.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
