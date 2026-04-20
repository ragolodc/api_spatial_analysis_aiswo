"""Dependency injection factories for elevation analysis module."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.modules.elevation.infrastructure.persistence import SQLAlchemyElevationSourceRepository
from src.modules.elevation_analysis.application.commands import (
    GenerateZoneContours,
    RunZoneElevationAnalysis,
)
from src.modules.elevation_analysis.application.queries import (
    GetZoneContours,
    ListZoneAnalyses,
)
from src.modules.elevation_analysis.infrastructure.persistence import (
    SQLAlchemyElevationAnalysisRepository,
    SQLAlchemyElevationContourRepository,
)
from src.modules.elevation_analysis.infrastructure.providers import (
    PlanetaryComputerAnalysisProvider,
)
from src.modules.zones.infrastructure.zone_geometry_adapter import SQLAlchemyZoneGeometryAdapter


def get_dem_provider(db: Session) -> PlanetaryComputerAnalysisProvider:
    """Resolve the active elevation source from DB and build the DEM provider."""
    repo = SQLAlchemyElevationSourceRepository(db)
    source = repo.find_active()
    if source is None:
        raise HTTPException(status_code=503, detail="No active elevation source configured")
    if not source.source_url or not source.collection:
        raise HTTPException(
            status_code=503, detail="Active elevation source is missing catalog_url or collection"
        )
    return PlanetaryComputerAnalysisProvider(
        catalog_url=source.source_url,
        collection=source.collection,
        source_id=source.id,
    )


def get_analysis_repository(db: Session) -> SQLAlchemyElevationAnalysisRepository:
    """Factory for elevation analysis repository."""
    return SQLAlchemyElevationAnalysisRepository(db)


def get_contour_repository(db: Session) -> SQLAlchemyElevationContourRepository:
    """Factory for elevation contour repository."""
    return SQLAlchemyElevationContourRepository(db)


def get_run_zone_elevation_analysis(db: Session) -> RunZoneElevationAnalysis:
    """Factory for RunZoneElevationAnalysis command."""
    return RunZoneElevationAnalysis(
        provider=get_dem_provider(db),
        analysis_repo=get_analysis_repository(db),
        zone_reader=SQLAlchemyZoneGeometryAdapter(db),
    )


def get_generate_zone_contours(db: Session) -> GenerateZoneContours:
    """Factory for GenerateZoneContours command."""
    return GenerateZoneContours(
        provider=get_dem_provider(db),
        contour_repo=get_contour_repository(db),
        zone_reader=SQLAlchemyZoneGeometryAdapter(db),
    )


def get_list_zone_analyses(db: Session) -> ListZoneAnalyses:
    """Factory for ListZoneAnalyses query."""
    analysis_repo = get_analysis_repository(db)
    return ListZoneAnalyses(analysis_repo)


def get_get_zone_contours(db: Session) -> GetZoneContours:
    """Factory for GetZoneContours query."""
    contour_repo = get_contour_repository(db)
    return GetZoneContours(contour_repo)
