"""Dependency injection factories for elevation analysis module."""

from sqlalchemy.orm import Session

from src.modules.elevation_analysis.application.commands import (
    GenerateZoneContours,
    RunZoneElevationAnalysis,
)
from src.modules.elevation_analysis.application.queries import (
    GetZoneContours,
    ListZoneAnalyses,
)
from src.modules.elevation_analysis.infrastructure.providers import get_dem_provider
from src.modules.elevation_analysis.infrastructure.persistence import (
    SQLAlchemyElevationAnalysisRepository,
    SQLAlchemyElevationContourRepository,
)
from src.modules.zones.infrastructure.persistence.zone_repository import (
    SQLAlchemyZoneRepository,
)


def get_zone_repository(db: Session):
    """Factory for zone repository."""
    return SQLAlchemyZoneRepository(db)


def get_analysis_repository(db: Session):
    """Factory for elevation analysis repository."""
    return SQLAlchemyElevationAnalysisRepository(db)


def get_contour_repository(db: Session):
    """Factory for elevation contour repository."""
    return SQLAlchemyElevationContourRepository(db)


def get_run_zone_elevation_analysis(db: Session) -> RunZoneElevationAnalysis:
    """Factory for RunZoneElevationAnalysis command."""
    provider = get_dem_provider()
    analysis_repo = get_analysis_repository(db)
    zone_repo = get_zone_repository(db)
    return RunZoneElevationAnalysis(provider, analysis_repo, zone_repo)


def get_generate_zone_contours(db: Session) -> GenerateZoneContours:
    """Factory for GenerateZoneContours command."""
    provider = get_dem_provider()
    contour_repo = get_contour_repository(db)
    zone_repo = get_zone_repository(db)
    return GenerateZoneContours(provider, contour_repo, zone_repo)


def get_list_zone_analyses(db: Session) -> ListZoneAnalyses:
    """Factory for ListZoneAnalyses query."""
    analysis_repo = get_analysis_repository(db)
    return ListZoneAnalyses(analysis_repo)


def get_get_zone_contours(db: Session) -> GetZoneContours:
    """Factory for GetZoneContours query."""
    contour_repo = get_contour_repository(db)
    return GetZoneContours(contour_repo)
