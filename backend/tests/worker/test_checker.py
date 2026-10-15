from collections.abc import Awaitable, Callable

import httpx
import pytest

from noar.worker.checker import run_http_check

Handler = Callable[[httpx.Request], Awaitable[httpx.Response]]

# allow_private=True below only skips the SSRF guard's DNS lookup, so these
# tests don't depend on real network access; the guard itself is covered in
# tests/security/test_ssrf.py.


def _client(handler: Handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_2xx_response_is_success() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    async with _client(handler) as client:
        outcome = await run_http_check(
            client, "https://example.com", timeout_seconds=5, allow_private=True
        )

    assert outcome.success is True
    assert outcome.status_code == 200
    assert outcome.error_message is None
    assert outcome.response_time_ms is not None


async def test_3xx_response_is_success_and_is_not_followed() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://10.0.0.1/internal"})

    async with _client(handler) as client:
        outcome = await run_http_check(
            client, "https://example.com", timeout_seconds=5, allow_private=True
        )

    assert outcome.success is True
    assert outcome.status_code == 302


async def test_5xx_response_is_failure() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    async with _client(handler) as client:
        outcome = await run_http_check(
            client, "https://example.com", timeout_seconds=5, allow_private=True
        )

    assert outcome.success is False
    assert outcome.status_code == 503
    assert outcome.error_message is not None


async def test_timeout_is_failure() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    async with _client(handler) as client:
        outcome = await run_http_check(
            client, "https://example.com", timeout_seconds=5, allow_private=True
        )

    assert outcome.success is False
    assert outcome.status_code is None
    assert outcome.error_message == "request timed out"


@pytest.mark.parametrize("url", ["ftp://example.com", "http://"])
async def test_blocked_url_fails_without_making_a_request(url: str) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not perform a request for a blocked URL")

    async with _client(handler) as client:
        outcome = await run_http_check(client, url, timeout_seconds=5, allow_private=True)

    assert outcome.success is False
    assert outcome.status_code is None
