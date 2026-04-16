import math

import planetary_computer
import pystac_client
import rioxarray  # noqa: F401 — registers the rioxarray accessor on xarray
from rioxarray.merge import merge_arrays
from shapely.geometry import Polygon

from src.modules.profile_analysis.domain.entities import ProfileSamplePoint
from src.modules.profile_analysis.domain.exceptions import DemNotAvailable

_ASSET_KEY = "data"
_PROVIDER_NAME = "planetary_computer"
_RESOLUTION_M = 30.0
_MAX_DEM_TILES = 16


class PlanetaryComputerProfileElevationProvider:
    """DEM batch sampler for generated profile points using Planetary Computer."""

    def __init__(self, catalog_url: str, collection: str) -> None:
        self._catalog_url = catalog_url
        self._collection = collection

    @property
    def name(self) -> str:
        return _PROVIDER_NAME

    @property
    def resolution_m(self) -> float:
        return _RESOLUTION_M

    def sample_points(self, points: list[ProfileSamplePoint]) -> list[ProfileSamplePoint]:
        if not points:
            return []

        bbox_polygon = self._build_bbox_polygon(points)
        catalog = pystac_client.Client.open(
            self._catalog_url,
            modifier=planetary_computer.sign_inplace,
        )
        items = list(
            catalog.search(
                collections=[self._collection],
                intersects=bbox_polygon,
                max_items=_MAX_DEM_TILES,
            ).items()
        )
        if not items:
            raise DemNotAvailable("No DEM coverage found for the requested profile points")

        tiles = [
            rioxarray.open_rasterio(item.assets[_ASSET_KEY].href, masked=True, lock=False)
            for item in items
        ]
        try:
            dem = merge_arrays(tiles) if len(tiles) > 1 else tiles[0]
            return [self._sample_point(dem, point) for point in points]
        finally:
            for tile in tiles:
                tile.close()

    def _sample_point(self, dem, point: ProfileSamplePoint) -> ProfileSamplePoint:
        raw_value = dem.sel(x=point.longitude, y=point.latitude, method="nearest").values[0]
        elevation = None if (raw_value is None or math.isnan(float(raw_value))) else float(raw_value)
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
        polygon = Polygon([
            (min(longitudes), min(latitudes)),
            (max(longitudes), min(latitudes)),
            (max(longitudes), max(latitudes)),
            (min(longitudes), max(latitudes)),
            (min(longitudes), min(latitudes)),
        ])
        return {"type": "Polygon", "coordinates": [list(polygon.exterior.coords)]}

