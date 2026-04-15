from fastapi import FastAPI

from src.modules.elevation.presentation.router import router as elevation_router
from src.shared.config.settings import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API para analisis espacial basada en FastAPI + PostGIS.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(elevation_router)
