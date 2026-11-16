import asyncio

import pytest

from noar.api import main as api_main
from noar.core.config import Settings


async def _idle(*_: object) -> None:
    await asyncio.Event().wait()


def _settings(**overrides: object) -> Settings:
    return api_main.settings.model_copy(update=overrides)


@pytest.mark.asyncio
async def test_scheduler_runs_inside_api_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def fake_scheduler(_: Settings) -> None:
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    monkeypatch.setattr(api_main, "settings", _settings(run_worker_in_api=True))
    monkeypatch.setattr(api_main, "run_listener", _idle)
    monkeypatch.setattr(api_main, "scheduler_loop", fake_scheduler)

    async with api_main.lifespan(api_main.app):
        await asyncio.wait_for(started.wait(), timeout=1)

    assert cancelled.is_set()


@pytest.mark.asyncio
async def test_scheduler_does_not_run_inside_api_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Settings] = []

    async def fake_scheduler(settings: Settings) -> None:
        calls.append(settings)

    monkeypatch.setattr(api_main, "settings", _settings(run_worker_in_api=False))
    monkeypatch.setattr(api_main, "run_listener", _idle)
    monkeypatch.setattr(api_main, "scheduler_loop", fake_scheduler)

    async with api_main.lifespan(api_main.app):
        await asyncio.sleep(0.05)

    assert calls == []
