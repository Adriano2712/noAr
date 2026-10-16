import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from noar.api.routers import auth, monitors, realtime, status
from noar.core.config import get_settings
from noar.realtime.hub import hub
from noar.realtime.listener import run_listener

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    listener_task = asyncio.create_task(run_listener(settings, hub))
    try:
        yield
    finally:
        listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await listener_task


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
