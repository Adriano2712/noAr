from httpx import AsyncClient


async def test_create_and_list_monitor(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("owner@example.com")

    create = await client.post(
        "/monitors",
        headers=headers,
        json={"name": "Example", "url": "https://example.com"},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["name"] == "Example"
    assert body["state"] == "unknown"

    listed = await client.get("/monitors", headers=headers)
    assert listed.status_code == 200
    assert [m["id"] for m in listed.json()] == [body["id"]]


async def test_create_monitor_rejects_blocked_url(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("blocked@example.com")

    response = await client.post(
        "/monitors",
        headers=headers,
        json={"name": "Internal", "url": "http://127.0.0.1:8000"},
    )

    assert response.status_code == 400


async def test_create_monitor_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/monitors", json={"name": "Example", "url": "https://example.com"}
    )

    assert response.status_code == 401


async def test_users_cannot_see_each_others_monitors(client: AsyncClient, auth_headers) -> None:
    headers_a = await auth_headers("a@example.com")
    headers_b = await auth_headers("b@example.com")

    create = await client.post(
        "/monitors",
        headers=headers_a,
        json={"name": "A's monitor", "url": "https://example.com"},
    )
    monitor_id = create.json()["id"]

    get_as_b = await client.get(f"/monitors/{monitor_id}", headers=headers_b)
    assert get_as_b.status_code == 404

    list_as_b = await client.get("/monitors", headers=headers_b)
    assert list_as_b.json() == []


async def test_update_monitor(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("updater@example.com")
    create = await client.post(
        "/monitors",
        headers=headers,
        json={"name": "Example", "url": "https://example.com"},
    )
    monitor_id = create.json()["id"]

    update = await client.patch(
        f"/monitors/{monitor_id}", headers=headers, json={"name": "Renamed"}
    )

    assert update.status_code == 200
    assert update.json()["name"] == "Renamed"


async def test_update_rejects_blocked_url(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("updater2@example.com")
    create = await client.post(
        "/monitors",
        headers=headers,
        json={"name": "Example", "url": "https://example.com"},
    )
    monitor_id = create.json()["id"]

    update = await client.patch(
        f"/monitors/{monitor_id}", headers=headers, json={"url": "http://169.254.169.254"}
    )

    assert update.status_code == 400


async def test_delete_monitor(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("deleter@example.com")
    create = await client.post(
        "/monitors",
        headers=headers,
        json={"name": "Example", "url": "https://example.com"},
    )
    monitor_id = create.json()["id"]

    delete = await client.delete(f"/monitors/{monitor_id}", headers=headers)
    assert delete.status_code == 204

    get_after = await client.get(f"/monitors/{monitor_id}", headers=headers)
    assert get_after.status_code == 404


async def test_pause_and_resume_monitor(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("pauser@example.com")
    create = await client.post(
        "/monitors",
        headers=headers,
        json={"name": "Example", "url": "https://example.com"},
    )
    monitor_id = create.json()["id"]

    paused = await client.post(f"/monitors/{monitor_id}/pause", headers=headers)
    assert paused.status_code == 200
    assert paused.json()["state"] == "paused"

    resumed = await client.post(f"/monitors/{monitor_id}/resume", headers=headers)
    assert resumed.status_code == 200
    assert resumed.json()["state"] == "unknown"
