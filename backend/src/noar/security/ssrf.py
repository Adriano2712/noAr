import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

ALLOWED_SCHEMES = frozenset({"http", "https"})

Resolver = Callable[[str], Awaitable[list[IPAddress]]]


class SSRFBlockedError(Exception):
    """Raised when a monitor URL is rejected to prevent server-side request forgery."""


async def _resolve_hostname(hostname: str) -> list[IPAddress]:
    infos = await asyncio.to_thread(socket.getaddrinfo, hostname, None)
    return [ipaddress.ip_address(info[4][0]) for info in infos]


def _is_blocked(ip: IPAddress) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


async def ensure_safe_url(
    url: str, *, allow_private: bool = False, resolver: Resolver = _resolve_hostname
) -> None:
    """Reject URLs that are not safe to request server-side.

    Blocks non-HTTP(S) schemes and any hostname that resolves to a private,
    loopback, link-local, reserved, multicast or unspecified address. This
    check runs right before each request but does not pin the resolved IP
    for the connection itself, so it does not fully close a DNS-rebinding
    window between this check and the actual HTTP request (see ADR 0005).

    `allow_private` exists only for the local Docker Compose demo, where the
    worker legitimately needs to reach `demo-target` on the compose network's
    private address range; it must stay off whenever monitor URLs can come
    from an untrusted user.
    """
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_SCHEMES:
        raise SSRFBlockedError(f"scheme not allowed: {parts.scheme!r}")
    if not parts.hostname:
        raise SSRFBlockedError("url has no hostname")

    if allow_private:
        return

    addresses = await resolver(parts.hostname)
    if not addresses:
        raise SSRFBlockedError(f"could not resolve hostname: {parts.hostname!r}")

    for ip in addresses:
        if _is_blocked(ip):
            raise SSRFBlockedError(f"resolved IP is not publicly routable: {ip}")
