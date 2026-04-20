import math
from uuid import UUID

import rioxarray  # noqa: F401 — registers the rioxarray accessor on xarray
from shapely.geometry import Polygon

from src.modules.profile_analysis.domain.entities import ProfileSamplePoint
from src.modules.profile_analysis.domain.exceptions import DemNotAvailable
from src.shared.infrastructure.dem.stac_dem_loader import fetch_dem_tiles, merge_dem_tiles

_PROVIDER_NAME = "planetary_computer"
_RESOLUTION_M = 30.0


class PlanetaryComputerProfileElevationProvider:
    """DEM batch sampler for generated profile points using Planetary Computer."""

    def __init__(self, catalog_url: str, collection: str, source_id: UUID) -> None:
        self._catalog_url = catalog_url
        self._collection = collection
        self._source_id = source_id

    def sample_points(self, points: list[ProfileSamplePoint]) -> list[ProfileSamplePoint]:
        if not points:
            return []

        bbox_polygon = self._build_bbox_polygon(points)
        tiles = fetch_dem_tiles(self._catalog_url, self._collection, bbox_polygon)
        if not tiles:
            raise DemNotAvailable("No DEM coverage found for the requested profile points")
        try:
            dem = merge_dem_tiles(tiles)
            return [self._sample_point(dem, point) for point in points]
        finally:
            for tile in tiles:
                tile.close()

    def _sample_point(self, dem, point: ProfileSamplePoint) -> ProfileSamplePoint:
        raw_value = dem.sel(x=point.longitude, y=point.latitude, method="nearest").values[0]
        elevation = (
            None if (raw_value is None or math.isnan(float(raw_value))) else float(raw_value)
        )
        return ProfileSamplePoint(
            longitude=point.longitude,
            latitude=point.latitude,
            distance_m=point.distance_m,
            radius_m=point.radius_m,
            angle_deg=point.angle_deg,
            elevation_m=elevation,
        )

    def _build_bbox_polygon(self, points: list[ProfileSamplePoint]) -> dict:
        longitudes = [p.longitude for p in points]
        latitudes = [p.latitude for p in points]
        polygon = Polygon(
            [
                (min(longitudes), min(latitudes)),
                (max(longitudes), min(latitudes)),
                (max(longitudes), max(latitudes)),
                (min(longitudes), max(latitudes)),
                (min(longitudes), min(latitudes)),
            ]
        )
        return {"type": "Polygon", "coordinates": [list(polygon.exterior.coords)]}
