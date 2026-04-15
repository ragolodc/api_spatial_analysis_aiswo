"""Adapter that exposes zone geometry to other bounded contexts.

This adapter lives in the zones slice because zones owns the geometry data.
It satisfies any ZoneGeometryReader port (Protocol) defined by consuming slices
via structural subtyping — no explicit import of those ports is required.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.zones.infrastructure.persistence.repository import SQLAlchemyZoneRepository
from src.shared.domain import GeoPolygon


class SQLAlchemyZoneGeometryAdapter:
    """
    Reads zone polygon geometry and returns a GeoPolygon.

    Can be used by any slice that defines a ZoneGeometryReader Protocol
    with the same interface (structural typing).
    """

    def __init__(self, db: Session) -> None:
        self._repo = SQLAlchemyZoneRepository(db)

    def find_polygon(self, zone_id: UUID) -> GeoPolygon | None:
        zone = self._repo.find_by_id(zone_id)
        if zone is None:
            return None
        return zone.geometry
