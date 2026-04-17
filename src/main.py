from fastapi import FastAPI

from src.modules.elevation.presentation.processes_router import router as elevation_processes_router
from src.modules.elevation.presentation.sources_router import router as elevation_sources_router
from src.modules.elevation_analysis.presentation.features_router import (
    router as elevation_analysis_features_router,
)
from src.modules.elevation_analysis.presentation.processes_router import (
    router as elevation_analysis_processes_router,
)
from src.modules.profile_analysis.presentation.processes_router import (
    router as profile_analysis_processes_router,
)
from src.modules.zones.presentation.features_router import router as zones_features_router
from src.shared.config import settings
from src.shared.presentation.ogc_landing_router import router as ogc_landing_router


def create_app(*, init_infraestructure: bool = True) -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API para analisis espacial basada en FastAPI + PostGIS.",
        swagger_ui_parameters={
            "syntaxHighlight": False,
            "defaultModelsExpandDepth": -1,
            "docExpansion": "none",
        },
    )

    API_V1_PREFIX = "/api/v1"

    @app.get(f"{API_V1_PREFIX}/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    API_V1_PREFIX = "/api/v1"

    app.include_router(ogc_landing_router, prefix=API_V1_PREFIX)
    app.include_router(zones_features_router, prefix=API_V1_PREFIX)
    app.include_router(elevation_sources_router, prefix=API_V1_PREFIX)
    app.include_router(elevation_analysis_features_router, prefix=API_V1_PREFIX)
    app.include_router(elevation_analysis_processes_router, prefix=API_V1_PREFIX)
    app.include_router(profile_analysis_processes_router, prefix=API_V1_PREFIX)
    app.include_router(elevation_processes_router, prefix=API_V1_PREFIX)

    return app


app = create_app()
