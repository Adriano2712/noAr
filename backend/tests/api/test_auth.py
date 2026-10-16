from httpx import AsyncClient


async def test_register_creates_a_user(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register", json={"email": "new@example.com", "password": "a-strong-password"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "a-strong-password"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 400


async def test_login_returns_a_bearer_token(client: AsyncClient) -> None:
    await client.post(
        "/auth/register", json={"email": "login@example.com", "password": "a-strong-password"}
    )

    response = await client.post(
        "/auth/login", data={"username": "login@example.com", "password": "a-strong-password"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/auth/register", json={"email": "wrong@example.com", "password": "a-strong-password"}
    )

    response = await client.post(
        "/auth/login", data={"username": "wrong@example.com", "password": "not-the-password"}
    )

    assert response.status_code == 401


async def test_login_rejects_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/login", data={"username": "ghost@example.com", "password": "whatever"}
    )

    assert response.status_code == 401


async def test_me_requires_a_token(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401


async def test_me_returns_the_current_user(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("me@example.com")

    response = await client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me@example.com"
    assert body["telegram_chat_id"] is None
    assert body["webhook_url"] is None


async def test_update_me_sets_notification_settings(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("settings@example.com")

    response = await client.patch(
        "/auth/me",
        headers=headers,
        json={"telegram_chat_id": "123456", "webhook_url": "https://example.com/hook"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["telegram_chat_id"] == "123456"
    assert body["webhook_url"] == "https://example.com/hook"


async def test_update_me_rejects_blocked_webhook_url(client: AsyncClient, auth_headers) -> None:
    headers = await auth_headers("blocked-webhook@example.com")

    response = await client.patch(
        "/auth/me", headers=headers, json={"webhook_url": "http://127.0.0.1:9999/hook"}
    )

    assert response.status_code == 400


async def test_update_me_clears_a_setting_with_explicit_null(
    client: AsyncClient, auth_headers
) -> None:
    headers = await auth_headers("clear-settings@example.com")
    await client.patch(
        "/auth/me", headers=headers, json={"telegram_chat_id": "123456"}
    )

    response = await client.patch("/auth/me", headers=headers, json={"telegram_chat_id": None})

    assert response.status_code == 200
    assert response.json()["telegram_chat_id"] is None


async def test_update_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.patch("/auth/me", json={"telegram_chat_id": "123456"})

    assert response.status_code == 401
