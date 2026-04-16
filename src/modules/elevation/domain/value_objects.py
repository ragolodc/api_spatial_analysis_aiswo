from dataclasses import dataclass
from typing import Any


@dataclass
class GeoPoint:
    longitude: float
    latitude: float

    def to_geojson(self) -> dict[str, Any]:
        return {"type": "Point", "coordinates": [self.longitude, self.latitude]}


@dataclass(frozen=True)
class Elevation:
    meters: float
