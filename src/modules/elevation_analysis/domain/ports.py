from typing import Protocol
from uuid import UUID

from src.shared.domain import GeoPolygon
from src.modules.elevation_analysis.domain.entities import (
    ElevationAnalysis,
    ElevationContour,
    PointType,
)


class ElevationAnalysisProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def resolution_m(self) -> float: ...

    def get_characteristic_points(
        self, polygon: GeoPolygon
    ) -> list[tuple[PointType, float, float, float]]:
        """Devuelve [(point_type, longitude, latitude, elevation_m), ...]."""
        ...

    def get_contours(
        self, polygon: GeoPolygon, interval_m: float
    ) -> list[tuple[float, dict]]:
        """Devuelve [(elevation_m, geojson_multilinestring), ...]."""
        ...


class ElevationAnalysisRepository(Protocol):
    def save(self, analysis: ElevationAnalysis) -> ElevationAnalysis: ...
    def find_by_id(self, analysis_id: UUID) -> ElevationAnalysis | None: ...
    def find_by_zone(self, zone_id: UUID) -> list[ElevationAnalysis]: ...


class ElevationContourRepository(Protocol):
    def save_all(self, contours: list[ElevationContour]) -> list[ElevationContour]: ...
    def find_by_zone(self, zone_id: UUID) -> list[ElevationContour]: ...
    def delete_by_zone(self, zone_id: UUID) -> None: ...


class ZoneGeometryReader(Protocol):
    """Narrow read port: get zone geometry without coupling to the zones module."""

    def find_polygon(self, zone_id: UUID) -> GeoPolygon | None: ...
