"""Shared domain value objects used across all bounded contexts."""

from src.shared.domain.exceptions import DemNotAvailable, ElevationSourceNotConfigured
from src.shared.domain.ports import ZoneGeometryReader
from src.shared.domain.value_objects import GeoMultiLineString, GeoPolygon

__all__ = [
    "GeoPolygon",
    "GeoMultiLineString",
    "ElevationSourceNotConfigured",
    "DemNotAvailable",
    "ZoneGeometryReader",
]
