from email.message import EmailMessage

import aiosmtplib

from noar.alerts.events import AlertContext, AlertEvent
from noar.core.config import Settings


def _subject(context: AlertContext) -> str:
    if context.event is AlertEvent.INCIDENT_OPENED:
        return f"[NoAr] {context.monitor_name} está fora do ar"
    return f"[NoAr] {context.monitor_name} voltou ao ar"


def _body(context: AlertContext) -> str:
    if context.event is AlertEvent.INCIDENT_OPENED:
        return (
            f'O monitor "{context.monitor_name}" ({context.monitor_url}) parou de '
            f"responder em {context.incident_started_at.isoformat()}."
        )
    resolved_at = (
        context.incident_resolved_at.isoformat() if context.incident_resolved_at else "agora"
    )
    return (
        f'O monitor "{context.monitor_name}" ({context.monitor_url}) voltou a '
        f"responder em {resolved_at}."
    )


async def send_email_alert(to_email: str, context: AlertContext, settings: Settings) -> None:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message["Subject"] = _subject(context)
    message.set_content(_body(context))

    await aiosmtplib.send(message, hostname=settings.smtp_host, port=settings.smtp_port)
