from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ZoneType(StrEnum):
    FARM_BOUNDARY = "farm_boundary"
    PIVOT = "pivot"


@dataclass
class Zone:
    id: UUID
    name: str
    zone_type: ZoneType
    geometry: dict
    created_at: datetime
