from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from src.shared.domain import GeoPolygon


class ZoneType(StrEnum):
    """Enumeration of supported zone types."""

    FARM_BOUNDARY = "farm_boundary"
    PIVOT = "pivot"


@dataclass
class Zone:
    """Geographic zone used as the spatial unit for analysis."""

    id: UUID
    name: str
    zone_type: ZoneType
    geometry: GeoPolygon
    created_at: datetime
