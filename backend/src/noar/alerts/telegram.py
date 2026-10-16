import logging

import httpx

from noar.alerts.events import AlertContext, AlertEvent
from noar.core.config import Settings

logger = logging.getLogger("noar.alerts.telegram")


def _text(context: AlertContext) -> str:
    if context.event is AlertEvent.INCIDENT_OPENED:
        return f"\U0001f534 {context.monitor_name} está fora do ar ({context.monitor_url})"
    return f"\U0001f7e2 {context.monitor_name} voltou ao ar ({context.monitor_url})"


async def send_telegram_alert(
    chat_id: str, context: AlertContext, settings: Settings, client: httpx.AsyncClient
) -> None:
    if not settings.telegram_bot_token:
        # The real bot is always optional (see ADR 0004); silently skipping
        # here, not raising, is what makes that true for this channel too.
        logger.info("skipping telegram alert: no bot token configured")
        return

    url = f"{settings.telegram_api_base_url}/bot{settings.telegram_bot_token}/sendMessage"
    response = await client.post(url, json={"chat_id": chat_id, "text": _text(context)})
    response.raise_for_status()
