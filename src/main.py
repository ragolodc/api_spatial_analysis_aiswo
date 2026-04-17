from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "details": details or {},
        },
    )


def _error_code_from_status(status_code: int) -> str:
    if status_code == 400:
        return "BAD_REQUEST"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 422:
        return "VALIDATION_ERROR"
    if status_code >= 500:
        return "INTERNAL_ERROR"
    return f"HTTP_{status_code}"


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    yield


def create_app(*, init_infraestructure: bool = True) -> FastAPI:

    API_V1_PREFIX = "/api/v1"

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API para analisis espacial basada en FastAPI + PostGIS.",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=_lifespan,
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
        message = str(exc.detail) if exc.detail is not None else "HTTP error"
        return _error_response(
            status_code=exc.status_code,
            code=_error_code_from_status(exc.status_code),
            message=message,
            details={},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        return _error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Invalid request payload or parameters.",
            details={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, _exc: Exception):
        return _error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Unexpected server error.",
            details={},
        )

    @app.get(f"{API_V1_PREFIX}/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(ogc_landing_router, prefix=API_V1_PREFIX)
    app.include_router(zones_features_router, prefix=API_V1_PREFIX)
    app.include_router(elevation_sources_router, prefix=API_V1_PREFIX)
    app.include_router(elevation_analysis_features_router, prefix=API_V1_PREFIX)
    app.include_router(elevation_analysis_processes_router, prefix=API_V1_PREFIX)
    app.include_router(profile_analysis_processes_router, prefix=API_V1_PREFIX)
    app.include_router(elevation_processes_router, prefix=API_V1_PREFIX)

    return app


app = create_app()
