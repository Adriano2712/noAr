from fastapi import HTTPException, status

from noar.core.config import Settings
from noar.security.ssrf import SSRFBlockedError, ensure_safe_url


async def validate_outbound_url(url: str, settings: Settings) -> None:
    """Reject a user-supplied URL the backend will later POST/GET to (monitor
    URL, webhook URL) with a 400 instead of letting it fail silently later."""
    try:
        await ensure_safe_url(url, allow_private=settings.ssrf_allow_private_networks)
    except SSRFBlockedError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
