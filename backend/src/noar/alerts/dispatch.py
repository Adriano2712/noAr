import logging

import httpx

from noar.alerts.email import send_email_alert
from noar.alerts.events import AlertContext
from noar.alerts.telegram import send_telegram_alert
from noar.alerts.webhook import send_webhook_alert
from noar.core.config import Settings
from noar.db.models import User

logger = logging.getLogger("noar.alerts")


async def dispatch_alert(
    user: User, context: AlertContext, settings: Settings, client: httpx.AsyncClient
) -> None:
    """Send `context` to every channel `user` has configured.

    Best-effort: a failing channel is logged and does not stop the others,
    and never propagates to the caller -- a dead Telegram bot or SMTP server
    must not stop the worker from processing checks.
    """
    try:
        await send_email_alert(user.email, context, settings)
    except Exception:
        logger.exception("failed to send email alert to %s", user.email)

    if user.telegram_chat_id:
        try:
            await send_telegram_alert(user.telegram_chat_id, context, settings, client)
        except Exception:
            logger.exception("failed to send telegram alert to chat %s", user.telegram_chat_id)

    if user.webhook_url:
        try:
            await send_webhook_alert(user.webhook_url, context, settings, client)
        except Exception:
            logger.exception("failed to send webhook alert to %s", user.webhook_url)
