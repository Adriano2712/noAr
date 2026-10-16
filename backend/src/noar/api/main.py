from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from noar.api.routers import auth, monitors
from noar.core.config import get_settings

settings = get_settings()

app = FastAPI(title="NoAr API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(monitors.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
