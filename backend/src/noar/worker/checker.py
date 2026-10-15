import time
from dataclasses import dataclass

import httpx

from noar.security.ssrf import SSRFBlockedError, ensure_safe_url


@dataclass(frozen=True)
class CheckOutcome:
    success: bool
    status_code: int | None
    response_time_ms: int | None
    error_message: str | None


async def run_http_check(
    client: httpx.AsyncClient, url: str, *, timeout_seconds: float, allow_private: bool
) -> CheckOutcome:
    """Perform one HTTP check. Never raises: every failure mode becomes a CheckOutcome.

    Redirects are not followed, so a 3xx response counts as success without
    ever requesting the redirect target — this is deliberate: it keeps a
    redirect from being used to reach a blocked address (see ssrf module).
    """
    try:
        await ensure_safe_url(url, allow_private=allow_private)
    except SSRFBlockedError as exc:
        return CheckOutcome(
            success=False, status_code=None, response_time_ms=None, error_message=str(exc)
        )

    started = time.monotonic()
    try:
        response = await client.get(url, timeout=timeout_seconds, follow_redirects=False)
    except httpx.TimeoutException:
        return CheckOutcome(
            success=False,
            status_code=None,
            response_time_ms=int((time.monotonic() - started) * 1000),
            error_message="request timed out",
        )
    except httpx.HTTPError as exc:
        return CheckOutcome(
            success=False,
            status_code=None,
            response_time_ms=int((time.monotonic() - started) * 1000),
            error_message=str(exc),
        )

    response_time_ms = int((time.monotonic() - started) * 1000)
    success = 200 <= response.status_code < 400
    return CheckOutcome(
        success=success,
        status_code=response.status_code,
        response_time_ms=response_time_ms,
        error_message=None if success else f"unexpected status code {response.status_code}",
    )
