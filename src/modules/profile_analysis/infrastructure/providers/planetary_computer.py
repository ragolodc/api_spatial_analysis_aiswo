import planetary_computer
import pystac_client
import rioxarray  # noqa: F401
from rioxarray.merge import merge_arrays
from shapely.geometry import Polygon

from src.modules.profile_analysis.domain.entities import ProfileSamplePoint
from src.modules.profile_analysis.domain.exceptions import DemNotAvailable

_ASSET_KEY = "data"


class PlanetaryComputerProfileElevationProvider:
    """DEM batch sampler for generated profile points using Planetary Computer."""

    def __init__(self, catalog_url: str, collection: str) -> None:
        self._catalog_url = catalog_url
        self._collection = collection

    @property
    def name(self) -> str:
        return "planetary_computer"

    @property
    def resolution_m(self) -> float:
        return 30.0

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
                max_items=16,
            ).items()
        )
        if not items:
            raise DemNotAvailable("No DEM coverage found for the requested profile points")

        tiles = [
            rioxarray.open_rasterio(item.assets[_ASSET_KEY].href, masked=True, lock=False)
            for item in items
        ]
        dem = merge_arrays(tiles) if len(tiles) > 1 else tiles[0]

        sampled_points: list[ProfileSamplePoint] = []
        for point in points:
            elevation = float(
                dem.sel(x=point.longitude, y=point.latitude, method="nearest").values[0]
            )
            sampled_points.append(
                ProfileSamplePoint(
                    longitude=point.longitude,
                    latitude=point.latitude,
                    distance_m=point.distance_m,
                    radius_m=point.radius_m,
                    angle_deg=point.angle_deg,
                    elevation_m=elevation,
                )
            )
        return sampled_points

    def _build_bbox_polygon(self, points: list[ProfileSamplePoint]) -> dict:
        longitudes = [point.longitude for point in points]
        latitudes = [point.latitude for point in points]
        min_lon = min(longitudes)
        max_lon = max(longitudes)
        min_lat = min(latitudes)
        max_lat = max(latitudes)
        polygon = Polygon([
            (min_lon, min_lat),
            (max_lon, min_lat),
            (max_lon, max_lat),
            (min_lon, max_lat),
            (min_lon, min_lat),
        ])
        return {"type": "Polygon", "coordinates": [list(polygon.exterior.coords)]}
