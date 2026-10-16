import httpx
import pytest

from noar.alerts.telegram import send_telegram_alert

from .conftest import make_context, make_settings


async def test_skips_when_no_bot_token_is_configured() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not call the telegram API without a bot token")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await send_telegram_alert(
            "123", make_context(), make_settings(telegram_bot_token=""), client
        )


async def test_sends_a_message_when_a_bot_token_is_configured() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await send_telegram_alert(
            "123", make_context(), make_settings(telegram_bot_token="secret-token"), client
        )

    assert len(requests) == 1
    assert "secret-token" in str(requests[0].url)


async def test_raises_on_an_http_error_so_dispatch_can_log_it() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await send_telegram_alert(
                "123", make_context(), make_settings(telegram_bot_token="secret-token"), client
            )
