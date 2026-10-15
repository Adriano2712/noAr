from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from noar.api.main import app
from noar.db.session import get_session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: AsyncClient):
    async def _make(email: str, password: str = "a-strong-password") -> dict[str, str]:
        response = await client.post(
            "/auth/register", json={"email": email, "password": password}
        )
        assert response.status_code == 201, response.text

        response = await client.post(
            "/auth/login", data={"username": email, "password": password}
        )
        assert response.status_code == 200, response.text
        token: str = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make
