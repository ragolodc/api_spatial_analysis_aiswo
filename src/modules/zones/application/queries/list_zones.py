"""Query: List all zones."""

from src.modules.zones.domain.entities import Zone
from src.modules.zones.domain.ports import ZoneRepository


class ListZones:
    """Query use case to list all stored zones."""

    def __init__(self, repository: ZoneRepository) -> None:
        self._repository = repository

    def execute(self) -> list[Zone]:
        return self._repository.find_all()
