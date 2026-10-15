import asyncio
import logging
import uuid

import httpx

from noar.core.config import Settings, get_settings
from noar.db.models import Monitor
from noar.db.session import async_session_factory
from noar.worker.claim import claim_due_monitors
from noar.worker.processor import process_monitor

logger = logging.getLogger("noar.worker")


async def _process_one(
    monitor_id: uuid.UUID, client: httpx.AsyncClient, settings: Settings
) -> None:
    async with async_session_factory() as session:
        monitor = await session.get(Monitor, monitor_id)
        if monitor is None:
            return
        try:
            await process_monitor(
                session,
                monitor,
                client,
                allow_private=settings.ssrf_allow_private_networks,
                jitter_fraction=settings.scheduler_jitter_fraction,
            )
        except Exception:
            logger.exception("check failed for monitor %s", monitor_id)
            return
        logger.info("checked monitor %s: state=%s", monitor.id, monitor.state)


async def run_once(client: httpx.AsyncClient, settings: Settings) -> int:
    async with async_session_factory() as session:
        monitors = await claim_due_monitors(
            session,
            limit=settings.scheduler_batch_size,
            lease_seconds=settings.scheduler_lease_seconds,
        )

    if not monitors:
        return 0

    semaphore = asyncio.Semaphore(settings.scheduler_check_concurrency)

    async def process_with_limit(monitor_id: uuid.UUID) -> None:
        async with semaphore:
            await _process_one(monitor_id, client, settings)

    await asyncio.gather(*(process_with_limit(monitor.id) for monitor in monitors))
    return len(monitors)


async def scheduler_loop(settings: Settings) -> None:
    async with httpx.AsyncClient() as client:
        while True:
            checked = await run_once(client, settings)
            if checked:
                logger.info("processed %d monitor(s)", checked)
            await asyncio.sleep(settings.scheduler_poll_interval_seconds)


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    logger.info("noar worker starting")
    asyncio.run(scheduler_loop(settings))


if __name__ == "__main__":
    main()
