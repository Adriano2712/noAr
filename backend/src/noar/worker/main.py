import asyncio
import logging

from sqlalchemy import text

from noar.core.config import get_settings
from noar.db.session import engine

logger = logging.getLogger("noar.worker")

HEARTBEAT_INTERVAL_SECONDS = 10


async def heartbeat_loop() -> None:
    while True:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        logger.info("worker heartbeat: database reachable")
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    logger.info("noar worker starting")
    asyncio.run(heartbeat_loop())


if __name__ == "__main__":
    main()
