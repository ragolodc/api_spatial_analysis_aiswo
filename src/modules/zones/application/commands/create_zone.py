"""Command: Create a new zone."""

from datetime import datetime, timezone
from uuid import uuid4

from src.modules.zones.domain.entities import Zone, ZoneType
from src.modules.zones.domain.ports import ZoneRepository


class CreateZone:
    """Command use case to create and persist a new zone."""

    def __init__(self, repository: ZoneRepository) -> None:
        self._repository = repository

    def execute(self, name: str, zone_type: ZoneType, geometry: dict) -> Zone:
        zone = Zone(
            id=uuid4(),
            name=name,
            zone_type=zone_type,
            geometry=geometry,
            created_at=datetime.now(timezone.utc),
        )
        return self._repository.save(zone)
