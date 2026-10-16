import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from noar.db.models import Check


async def _create_monitor(
    client: AsyncClient, headers: dict[str, str], *, name: str = "Example"
) -> str:
    response = await client.post(
        "/monitors", headers=headers, json={"name": name, "url": "https://example.com"}
    )
    assert response.status_code == 201
    monitor_id: str = response.json()["id"]
    return monitor_id


async def test_status_page_only_lists_public_monitors(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("status@example.com")
    public_id = await _create_monitor(client, headers, name="Public one")
    private_id = await _create_monitor(client, headers, name="Private one")

    await client.patch(f"/monitors/{public_id}", headers=headers, json={"is_public": True})

    me = await client.get("/auth/me", headers=headers)
    owner_id = me.json()["id"]

    response = await client.get(f"/status/{owner_id}")

    assert response.status_code == 200
    body = response.json()
    names = [m["name"] for m in body["monitors"]]
    assert names == ["Public one"]
    assert private_id not in [m["id"] for m in body["monitors"]]


async def test_status_page_is_empty_for_an_unknown_owner(client: AsyncClient) -> None:
    response = await client.get(f"/status/{uuid.uuid4()}")

    assert response.status_code == 200
    assert response.json() == {"monitors": []}


async def test_status_page_requires_no_authentication(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("no-auth-needed@example.com")
    monitor_id = await _create_monitor(client, headers)
    await client.patch(f"/monitors/{monitor_id}", headers=headers, json={"is_public": True})
    me = await client.get("/auth/me", headers=headers)
    owner_id = me.json()["id"]

    response = await client.get(f"/status/{owner_id}")  # no Authorization header

    assert response.status_code == 200
    assert len(response.json()["monitors"]) == 1


async def test_status_page_reports_uptime_percentage(
    client: AsyncClient, auth_headers, db_session: AsyncSession
) -> None:
    headers = await auth_headers("uptime@example.com")
    monitor_id = await _create_monitor(client, headers)
    await client.patch(f"/monitors/{monitor_id}", headers=headers, json={"is_public": True})
    me = await client.get("/auth/me", headers=headers)
    owner_id = me.json()["id"]

    now = datetime.now(UTC)
    db_session.add_all(
        [
            Check(
                monitor_id=uuid.UUID(monitor_id),
                started_at=now - timedelta(minutes=i),
                finished_at=now - timedelta(minutes=i),
                success=i != 0,
                status_code=200 if i != 0 else 500,
                response_time_ms=100,
                error_message=None,
            )
            for i in range(4)
        ]
    )
    await db_session.flush()

    response = await client.get(f"/status/{owner_id}")

    assert response.status_code == 200
    monitor = response.json()["monitors"][0]
    assert monitor["uptime_percentage"] == 75.0


async def test_status_page_has_no_uptime_without_checks(
    client: AsyncClient, auth_headers
) -> None:
    headers = await auth_headers("no-checks@example.com")
    monitor_id = await _create_monitor(client, headers)
    await client.patch(f"/monitors/{monitor_id}", headers=headers, json={"is_public": True})
    me = await client.get("/auth/me", headers=headers)
    owner_id = me.json()["id"]

    response = await client.get(f"/status/{owner_id}")

    assert response.json()["monitors"][0]["uptime_percentage"] is None
