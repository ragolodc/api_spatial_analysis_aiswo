"""Dependency injection factories for elevation module."""

from sqlalchemy.orm import Session

from src.modules.elevation.application.queries import (
    GetHighestPointInPolygon,
    GetPointElevation,
    ListElevationSources,
)
from src.modules.elevation.infrastructure.providers.planetary_computer import (
    PlanetaryComputerElevationProvider,
)


def get_elevation_provider() -> PlanetaryComputerElevationProvider:
    """Factory for elevation DEM provider."""
    return PlanetaryComputerElevationProvider()


def get_get_highest_point() -> GetHighestPointInPolygon:
    """Factory for GetHighestPointInPolygon query."""
    return GetHighestPointInPolygon(get_elevation_provider())


def get_get_point_elevation() -> GetPointElevation:
    """Factory for GetPointElevation query."""
    return GetPointElevation(get_elevation_provider())


def get_list_elevation_sources(db: Session) -> ListElevationSources:
    """Factory for ListElevationSources query."""
    return ListElevationSources(db)
