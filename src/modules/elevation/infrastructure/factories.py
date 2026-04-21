"""Dependency injection factories for elevation module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.modules.elevation.application.queries import (
    GetHighestPointInPolygon,
    GetPointElevation,
    ListElevationSources,
)
from src.modules.elevation.infrastructure.persistence import (
    SQLAlchemyElevationSourceRepository,
)
from src.modules.elevation.infrastructure.providers.planetary_computer import (
    PlanetaryComputerElevationProvider,
)
from src.modules.zones.infrastructure.zone_geometry_adapter import SQLAlchemyZoneGeometryAdapter
from src.shared.db.session import get_db
from src.shared.domain import ElevationSourceNotConfigured


def get_elevation_provider(db: Session) -> PlanetaryComputerElevationProvider:
    """Resolve the active elevation source from DB and build the DEM provider."""
    repo = SQLAlchemyElevationSourceRepository(db)
    source = repo.find_active()
    if source is None:
        raise ElevationSourceNotConfigured("No active elevation source configured")
    if not source.source_url or not source.collection:
        raise ElevationSourceNotConfigured(
            "Active elevation source is missing catalog_url or collection"
        )
    return PlanetaryComputerElevationProvider(
        catalog_url=source.source_url,
        collection=source.collection,
        source_id=source.id,
    )


def get_get_highest_point(db: Session = Depends(get_db)) -> GetHighestPointInPolygon:
    """Factory for GetHighestPointInPolygon query."""
    return GetHighestPointInPolygon(get_elevation_provider(db))


def get_get_point_elevation(db: Session = Depends(get_db)) -> GetPointElevation:
    """Factory for GetPointElevation query."""
    return GetPointElevation(get_elevation_provider(db))


def get_list_elevation_sources(db: Session = Depends(get_db)) -> ListElevationSources:
    """Factory for ListElevationSources query."""
    return ListElevationSources(SQLAlchemyElevationSourceRepository(db))


def get_zone_geometry_reader(db: Session = Depends(get_db)) -> SQLAlchemyZoneGeometryAdapter:
    """Factory for ZoneGeometryReader ACL adapter."""
    return SQLAlchemyZoneGeometryAdapter(db)


def get_elevation_source_reader(
    db: Session = Depends(get_db),
) -> SQLAlchemyElevationSourceRepository:
    """Factory for ElevationSourceReader port — provides the active source resolver."""
    return SQLAlchemyElevationSourceRepository(db)
