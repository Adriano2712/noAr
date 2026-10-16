import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from noar.db.models import Check, Incident


async def _create_monitor(client: AsyncClient, headers: dict[str, str]) -> uuid.UUID:
    response = await client.post(
        "/monitors",
        headers=headers,
        json={"name": "Example", "url": "https://example.com"},
    )
    assert response.status_code == 201
    return uuid.UUID(response.json()["id"])


async def test_list_checks_returns_recent_checks(
    client: AsyncClient, auth_headers, db_session: AsyncSession
) -> None:
    headers = await auth_headers("history@example.com")
    monitor_id = await _create_monitor(client, headers)

    now = datetime.now(UTC)
    db_session.add_all(
        [
            Check(
                monitor_id=monitor_id,
                started_at=now - timedelta(minutes=i),
                finished_at=now - timedelta(minutes=i),
                success=i % 2 == 0,
                status_code=200 if i % 2 == 0 else 500,
                response_time_ms=100 + i,
                error_message=None,
            )
            for i in range(3)
        ]
    )
    await db_session.flush()

    response = await client.get(f"/monitors/{monitor_id}/checks", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    # newest first
    assert body[0]["response_time_ms"] == 100


async def test_list_checks_respects_limit(
    client: AsyncClient, auth_headers, db_session: AsyncSession
) -> None:
    headers = await auth_headers("limit@example.com")
    monitor_id = await _create_monitor(client, headers)

    now = datetime.now(UTC)
    db_session.add_all(
        [
            Check(
                monitor_id=monitor_id,
                started_at=now - timedelta(minutes=i),
                finished_at=now - timedelta(minutes=i),
                success=True,
                status_code=200,
                response_time_ms=100,
                error_message=None,
            )
            for i in range(5)
        ]
    )
    await db_session.flush()

    response = await client.get(
        f"/monitors/{monitor_id}/checks", headers=headers, params={"limit": 2}
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_checks_requires_ownership(
    client: AsyncClient, auth_headers, db_session: AsyncSession
) -> None:
    owner_headers = await auth_headers("history-owner@example.com")
    other_headers = await auth_headers("history-other@example.com")
    monitor_id = await _create_monitor(client, owner_headers)

    response = await client.get(f"/monitors/{monitor_id}/checks", headers=other_headers)

    assert response.status_code == 404


async def test_list_incidents_newest_first(
    client: AsyncClient, auth_headers, db_session: AsyncSession
) -> None:
    headers = await auth_headers("incidents@example.com")
    monitor_id = await _create_monitor(client, headers)

    now = datetime.now(UTC)
    older = Incident(monitor_id=monitor_id, started_at=now - timedelta(hours=2))
    newer = Incident(monitor_id=monitor_id, started_at=now - timedelta(minutes=5))
    db_session.add_all([older, newer])
    await db_session.flush()

    response = await client.get(f"/monitors/{monitor_id}/incidents", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert [row["id"] for row in body] == [str(newer.id), str(older.id)]
    assert body[0]["resolved_at"] is None


async def test_list_incidents_requires_ownership(
    client: AsyncClient, auth_headers, db_session: AsyncSession
) -> None:
    owner_headers = await auth_headers("incidents-owner@example.com")
    other_headers = await auth_headers("incidents-other@example.com")
    monitor_id = await _create_monitor(client, owner_headers)

    response = await client.get(f"/monitors/{monitor_id}/incidents", headers=other_headers)

    assert response.status_code == 404


async def test_unknown_monitor_id_returns_404(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("unknown@example.com")

    response = await client.get(
        "/monitors/00000000-0000-0000-0000-000000000000/checks", headers=headers
    )

    assert response.status_code == 404

