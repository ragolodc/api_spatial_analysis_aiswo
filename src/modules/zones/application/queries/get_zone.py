"""Query: Get zone by id."""

from uuid import UUID

from src.modules.zones.domain.entities import Zone
from src.modules.zones.domain.ports import ZoneRepository


class GetZone:
    """Query use case to retrieve a zone by its ID."""

    def __init__(self, repository: ZoneRepository) -> None:
        self._repository = repository

    def execute(self, zone_id: UUID) -> Zone | None:
        return self._repository.find_by_id(zone_id)
