import httpx

from noar.alerts.dispatch import dispatch_alert
from noar.db.models import User

from .conftest import make_context, make_settings


def _user(**overrides: object) -> User:
    defaults: dict[str, object] = {"email": "user@example.com"}
    defaults.update(overrides)
    return User(**defaults)  # type: ignore[arg-type]


def _no_http_client() -> httpx.AsyncClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected HTTP call to {request.url}")

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_sends_only_email_when_no_other_channel_is_configured(monkeypatch) -> None:
    sent: list[str] = []

    async def fake_email(to_email: str, context: object, settings: object) -> None:
        sent.append(to_email)

    monkeypatch.setattr("noar.alerts.dispatch.send_email_alert", fake_email)

    async with _no_http_client() as client:
        await dispatch_alert(_user(), make_context(), make_settings(), client)

    assert sent == ["user@example.com"]


async def test_sends_telegram_and_webhook_when_configured(monkeypatch) -> None:
    sent: list[str] = []

    async def fake_email(*args: object, **kwargs: object) -> None:
        sent.append("email")

    async def fake_telegram(*args: object, **kwargs: object) -> None:
        sent.append("telegram")

    async def fake_webhook(*args: object, **kwargs: object) -> None:
        sent.append("webhook")

    monkeypatch.setattr("noar.alerts.dispatch.send_email_alert", fake_email)
    monkeypatch.setattr("noar.alerts.dispatch.send_telegram_alert", fake_telegram)
    monkeypatch.setattr("noar.alerts.dispatch.send_webhook_alert", fake_webhook)

    user = _user(telegram_chat_id="123", webhook_url="https://example.com/hook")

    async with _no_http_client() as client:
        await dispatch_alert(user, make_context(), make_settings(), client)

    assert sorted(sent) == ["email", "telegram", "webhook"]


async def test_a_failing_channel_does_not_stop_the_others_or_raise(monkeypatch) -> None:
    sent: list[str] = []

    async def failing_email(*args: object, **kwargs: object) -> None:
        raise RuntimeError("smtp is down")

    async def fake_telegram(*args: object, **kwargs: object) -> None:
        sent.append("telegram")

    async def failing_webhook(*args: object, **kwargs: object) -> None:
        raise RuntimeError("webhook is down")

    monkeypatch.setattr("noar.alerts.dispatch.send_email_alert", failing_email)
    monkeypatch.setattr("noar.alerts.dispatch.send_telegram_alert", fake_telegram)
    monkeypatch.setattr("noar.alerts.dispatch.send_webhook_alert", failing_webhook)

    user = _user(telegram_chat_id="123", webhook_url="https://example.com/hook")

    async with _no_http_client() as client:
        await dispatch_alert(user, make_context(), make_settings(), client)  # must not raise

    assert sent == ["telegram"]
