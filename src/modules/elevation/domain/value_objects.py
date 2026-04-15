from dataclasses import dataclass


@dataclass
class GeoPoint:
    longitude: float
    latitude: float

    def to_geojson(self) -> dict:
        return {"type": "Point", "coordinates": [self.longitude, self.latitude]}


@dataclass(frozen=True)
class Elevation:
    meters: float
