"""Adapter that exposes zone geometry to other bounded contexts.

This adapter lives in the zones slice because zones owns the geometry data.
It satisfies the canonical ZoneGeometryReader port defined in src.shared.domain.ports
via structural subtyping — no explicit import of that port is required here.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.zones.infrastructure.persistence.repository import SQLAlchemyZoneRepository
from src.shared.domain import GeoPolygon


class SQLAlchemyZoneGeometryAdapter:
    """
    Reads zone polygon geometry and returns a GeoPolygon.

    Satisfies the ZoneGeometryReader port (src.shared.domain.ports) via structural typing.
    """

    def __init__(self, db: Session) -> None:
        self._repo = SQLAlchemyZoneRepository(db)

    def find_polygon(self, zone_id: UUID) -> GeoPolygon | None:
        zone = self._repo.find_by_id(zone_id)
        if zone is None:
            return None
        return zone.geometry
