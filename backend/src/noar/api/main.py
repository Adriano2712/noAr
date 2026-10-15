from fastapi import FastAPI

app = FastAPI(title="NoAr API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
