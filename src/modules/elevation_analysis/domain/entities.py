from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from src.shared.domain import GeoMultiLineString


class PointType(StrEnum):
    HIGHEST = "highest"
    LOWEST = "lowest"
    CENTROID = "centroid"


@dataclass
class ElevationPoint:
    """Punto característico de un análisis de elevación (más alto, más bajo, centroide)."""

    id: UUID
    analysis_id: UUID
    point_type: PointType
    longitude: float
    latitude: float
    elevation_m: float


@dataclass
class ElevationAnalysis:
    """Registro de un análisis de elevación ejecutado sobre una zona."""

    id: UUID
    zone_id: UUID
    provider: str
    resolution_m: float
    analyzed_at: datetime
    points: list[ElevationPoint] = field(default_factory=list)


@dataclass
class ElevationContour:
    """Curva de nivel derivada del DEM para una zona."""

    id: UUID
    zone_id: UUID
    provider: str
    interval_m: float
    elevation_m: float
    geometry: GeoMultiLineString  # GeoJSON MultiLineString
    generated_at: datetime
