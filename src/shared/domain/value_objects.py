"""Shared domain value objects used across multiple modules."""

from dataclasses import dataclass
from typing import Any


@dataclass
class GeoPoint:
    """Geographic point expressed as longitude/latitude."""

    longitude: float
    latitude: float

    def to_geojson(self) -> dict[str, Any]:
        return {"type": "Point", "coordinates": [self.longitude, self.latitude]}


@dataclass
class GeoPolygon:
    """Geographic polygon expressed as GeoJSON-style nested coordinate list."""

    coordinates: list[list[list[float]]]

    def to_geojson(self) -> dict[str, Any]:
        return {"type": "Polygon", "coordinates": self.coordinates}


@dataclass
class GeoMultiLineString:
    """Geographic multi-line string expressed as GeoJSON-style nested coordinate list."""

    coordinates: list[list[list[float]]]

    def to_geojson(self) -> dict[str, Any]:
        return {"type": "MultiLineString", "coordinates": self.coordinates}
