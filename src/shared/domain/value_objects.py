"""Shared domain value objects used across multiple modules."""

from dataclasses import dataclass


@dataclass
class GeoPolygon:
    """Geographic polygon expressed as GeoJSON-style nested coordinate list."""

    coordinates: list[list[list[float]]]

    def to_geojson(self) -> dict:
        return {"type": "Polygon", "coordinates": self.coordinates}


@dataclass
class GeoMultiLineString:
    """Geographic multi-line string expressed as GeoJSON-style nested coordinate list."""

    coordinates: list[list[list[float]]]

    def to_geojson(self) -> dict:
        return {"type": "MultiLineString", "coordinates": self.coordinates}
