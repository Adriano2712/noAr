import asyncio

import httpx
import pytest

from noar.api.main import settings as base_settings
from noar.core.config import Settings
from noar.worker import main as worker_main


@pytest.mark.asyncio
async def test_scheduler_loop_survives_a_failed_round(monkeypatch: pytest.MonkeyPatch) -> None:
    rounds = 0
    third_round = asyncio.Event()

    async def flaky_run_once(_: httpx.AsyncClient, __: Settings) -> int:
        nonlocal rounds
        rounds += 1
        if rounds == 1:
            raise ConnectionError("database unreachable")
        if rounds >= 3:
            third_round.set()
        return 0

    monkeypatch.setattr(worker_main, "run_once", flaky_run_once)
    settings = base_settings.model_copy(update={"scheduler_poll_interval_seconds": 0.01})

    task = asyncio.create_task(worker_main.scheduler_loop(settings))
    try:
        await asyncio.wait_for(third_round.wait(), timeout=15)
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert rounds >= 3
