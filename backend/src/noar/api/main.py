import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from noar.api.routers import auth, monitors, realtime, status
from noar.core.config import get_settings
from noar.realtime.hub import hub
from noar.realtime.listener import run_listener
from noar.worker.main import scheduler_loop

settings = get_settings()
logger = logging.getLogger("noar.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    tasks = [asyncio.create_task(run_listener(settings, hub))]
    if settings.run_worker_in_api:
        # Same logging the standalone worker sets up in noar.worker.main.main;
        # uvicorn only configures its own loggers, so without this the
        # scheduler's INFO lines would never reach the platform's log stream.
        logging.basicConfig(level=settings.log_level)
        logger.info("running the scheduler inside the API process")
        tasks.append(asyncio.create_task(scheduler_loop(settings)))
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="NoAr API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
# Before monitors.router: Starlette matches routes in registration order, and
# "/monitors/{monitor_id}" would otherwise swallow "/monitors/stream" first,
# treating "stream" as a monitor_id and failing UUID validation (422) instead
# of ever reaching this SSE route.
app.include_router(realtime.router)
app.include_router(monitors.router)
app.include_router(status.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
