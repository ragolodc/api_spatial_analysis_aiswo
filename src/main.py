from fastapi import FastAPI

from src.modules.elevation.presentation.ogc_router import router as ogc_router
from src.modules.elevation.presentation.router import router as elevation_router
from src.modules.elevation_analysis.presentation.router import router as elevation_analysis_router
from src.modules.zones.presentation.router import router as zones_router
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
app.include_router(ogc_router)
app.include_router(zones_router)
app.include_router(elevation_analysis_router)
