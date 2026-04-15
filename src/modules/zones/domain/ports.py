from typing import Protocol
from uuid import UUID

from src.modules.zones.domain.entities import Zone


class ZoneRepository(Protocol):
    """Port defining persistence operations for Zone aggregate."""

    def save(self, zone: Zone) -> Zone: ...
    def find_by_id(self, zone_id: UUID) -> Zone | None: ...
    def find_all(self) -> list[Zone]: ...
