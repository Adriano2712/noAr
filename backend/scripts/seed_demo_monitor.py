"""Seed a demo user and a monitor pointing at the demo-target service.

There is no monitor CRUD API yet (Fase 2 only builds the scheduler), so this
is how we get a monitor into the database to watch the worker check it,
open an incident when demo-target goes down, and recover when it comes
back. Safe to run more than once: it reuses the existing row by email/url
instead of creating duplicates.

Usage: uv run python scripts/seed_demo_monitor.py
"""

import asyncio

from sqlalchemy import select

from noar.core.config import get_settings
from noar.db.models import Monitor, User
from noar.db.session import async_session_factory

DEMO_EMAIL = "demo@noar.local"


async def seed() -> None:
    settings = get_settings()

    async with async_session_factory() as session:
        user = await session.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(email=DEMO_EMAIL)
            session.add(user)
            await session.flush()
            print(f"created user {DEMO_EMAIL}")

        monitor = await session.scalar(
            select(Monitor).where(
                Monitor.owner_id == user.id, Monitor.url == settings.demo_target_url
            )
        )
        if monitor is None:
            monitor = Monitor(
                owner_id=user.id,
                name="demo-target",
                url=settings.demo_target_url,
                interval_seconds=15,
                timeout_seconds=5,
                fail_threshold=2,
            )
            session.add(monitor)
            print(f"created monitor for {settings.demo_target_url}")
        else:
            print(f"monitor for {settings.demo_target_url} already exists")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
