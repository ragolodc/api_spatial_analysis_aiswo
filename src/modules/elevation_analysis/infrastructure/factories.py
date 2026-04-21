"""Dependency injection factories for elevation analysis module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.modules.elevation.infrastructure.factories import get_elevation_source_reader
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
from src.shared.db.session import get_db
from src.shared.domain import ElevationSourceNotConfigured, ElevationSourceReader


def get_dem_provider(source_reader: ElevationSourceReader) -> PlanetaryComputerAnalysisProvider:
    """Resolve the active elevation source from DB and build the DEM provider."""

    source = source_reader.find_active()
    if source is None:
        raise ElevationSourceNotConfigured("No active elevation source configured")
    if not source.source_url or not source.collection:
        raise ElevationSourceNotConfigured(
            "Active elevation source is missing catalog_url or collection"
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


def get_run_zone_elevation_analysis(
    db: Session = Depends(get_db),
    source_reader: ElevationSourceReader = Depends(get_elevation_source_reader),
) -> RunZoneElevationAnalysis:
    """Factory for RunZoneElevationAnalysis command."""
    return RunZoneElevationAnalysis(
        provider=get_dem_provider(source_reader),
        analysis_repo=get_analysis_repository(db),
        zone_reader=SQLAlchemyZoneGeometryAdapter(db),
    )


def get_generate_zone_contours(
    db: Session = Depends(get_db),
    source_reader: ElevationSourceReader = Depends(get_elevation_source_reader),
) -> GenerateZoneContours:
    """Factory for GenerateZoneContours command."""
    return GenerateZoneContours(
        provider=get_dem_provider(source_reader),
        contour_repo=get_contour_repository(db),
        zone_reader=SQLAlchemyZoneGeometryAdapter(db),
    )


def get_list_zone_analyses(db: Session = Depends(get_db)) -> ListZoneAnalyses:
    """Factory for ListZoneAnalyses query."""
    analysis_repo = get_analysis_repository(db)
    return ListZoneAnalyses(analysis_repo)


def get_get_zone_contours(db: Session = Depends(get_db)) -> GetZoneContours:
    """Factory for GetZoneContours query."""
    contour_repo = get_contour_repository(db)
    return GetZoneContours(contour_repo)
