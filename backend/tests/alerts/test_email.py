from unittest.mock import AsyncMock, patch

from noar.alerts.email import send_email_alert
from noar.alerts.events import AlertEvent

from .conftest import make_context, make_settings


async def test_sends_an_email_for_an_opened_incident() -> None:
    with patch("noar.alerts.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await send_email_alert(
            "user@example.com",
            make_context(AlertEvent.INCIDENT_OPENED),
            make_settings(smtp_host="mailpit", smtp_port=1025, smtp_from="noar@localhost"),
        )

    mock_send.assert_awaited_once()
    message = mock_send.call_args.args[0]
    assert message["To"] == "user@example.com"
    assert message["From"] == "noar@localhost"
    assert "fora do ar" in message["Subject"]
    assert mock_send.call_args.kwargs == {"hostname": "mailpit", "port": 1025}


async def test_sends_an_email_for_a_closed_incident() -> None:
    with patch("noar.alerts.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await send_email_alert(
            "user@example.com", make_context(AlertEvent.INCIDENT_CLOSED), make_settings()
        )

    message = mock_send.call_args.args[0]
    assert "voltou ao ar" in message["Subject"]
