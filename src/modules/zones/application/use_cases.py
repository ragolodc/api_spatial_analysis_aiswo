from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.modules.zones.domain.entities import Zone, ZoneType
from src.modules.zones.domain.ports import ZoneRepository


class CreateZone:
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


class GetZone:
    def __init__(self, repository: ZoneRepository) -> None:
        self._repository = repository

    def execute(self, zone_id: UUID) -> Zone | None:
        return self._repository.find_by_id(zone_id)


class ListZones:
    def __init__(self, repository: ZoneRepository) -> None:
        self._repository = repository

    def execute(self) -> list[Zone]:
        return self._repository.find_all()
