import httpx
import pytest

from noar.alerts.webhook import send_webhook_alert
from noar.security.ssrf import SSRFBlockedError

from .conftest import make_context, make_settings


async def test_posts_the_event_payload_to_the_webhook() -> None:
    bodies: list[bytes] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(await request.aread())
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await send_webhook_alert(
            "https://example.com/hook", make_context(), make_settings(), client
        )

    assert len(bodies) == 1
    assert b"incident_opened" in bodies[0]


async def test_blocks_a_disallowed_url_without_making_a_request() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not call a blocked webhook url")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SSRFBlockedError):
            await send_webhook_alert(
                "http://127.0.0.1:9999/hook", make_context(), make_settings(), client
            )
