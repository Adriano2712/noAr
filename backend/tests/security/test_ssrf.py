import ipaddress

import pytest

from noar.security.ssrf import SSRFBlockedError, ensure_safe_url


def _fake_resolver(*ips: str):
    async def resolver(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        return [ipaddress.ip_address(ip) for ip in ips]

    return resolver


async def test_allows_public_ip() -> None:
    await ensure_safe_url("https://example.com", resolver=_fake_resolver("93.184.216.34"))


@pytest.mark.parametrize(
    "blocked_ip",
    [
        "10.0.0.5",  # RFC1918 private
        "172.18.0.2",  # RFC1918 private (docker's default bridge range)
        "192.168.1.1",  # RFC1918 private
        "127.0.0.1",  # loopback
        "169.254.1.1",  # link-local
        "0.0.0.0",  # unspecified
        "::1",  # IPv6 loopback
    ],
)
async def test_blocks_non_public_ip(blocked_ip: str) -> None:
    with pytest.raises(SSRFBlockedError):
        await ensure_safe_url("https://internal.example", resolver=_fake_resolver(blocked_ip))


async def test_blocks_disallowed_scheme() -> None:
    with pytest.raises(SSRFBlockedError):
        await ensure_safe_url("ftp://example.com", resolver=_fake_resolver("93.184.216.34"))


async def test_blocks_url_without_hostname() -> None:
    with pytest.raises(SSRFBlockedError):
        await ensure_safe_url("http://", resolver=_fake_resolver("93.184.216.34"))


async def test_blocks_unresolvable_hostname() -> None:
    with pytest.raises(SSRFBlockedError):
        await ensure_safe_url("https://does-not-resolve.example", resolver=_fake_resolver())


async def test_allow_private_bypasses_resolution() -> None:
    async def failing_resolver(hostname: str) -> list[ipaddress.IPv4Address]:
        raise AssertionError("resolver should not be called when allow_private=True")

    await ensure_safe_url(
        "http://demo-target", allow_private=True, resolver=failing_resolver
    )
