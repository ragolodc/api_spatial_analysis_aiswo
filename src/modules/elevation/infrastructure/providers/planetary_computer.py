import numpy as np
import planetary_computer
import pystac_client
import rioxarray  # noqa: F401  — registers .rio accessor on xarray DataArray
from rioxarray.merge import merge_arrays

from src.modules.elevation.domain.exceptions import ElevationDataNotFound
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint, GeoPolygon

_CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
_COLLECTION = "cop-dem-glo-30"
_ASSET_KEY = "data"


class PlanetaryComputerElevationProvider:

    def _find_items(self, geometry: dict) -> list:
        catalog = pystac_client.Client.open(
            _CATALOG_URL, modifier=planetary_computer.sign_inplace
        )
        items = list(
            catalog.search(
                collections=[_COLLECTION], intersects=geometry, max_items=16
            ).items()
        )
        if not items:
            raise ElevationDataNotFound("No DEM coverage found for the given geometry")
        return items

    def get_highest_point(self, polygon: GeoPolygon) -> tuple[GeoPoint, Elevation]:
        geojson = polygon.to_geojson()
        items = self._find_items(geojson)

        tiles = [
            rioxarray.open_rasterio(item.assets[_ASSET_KEY].href, masked=True, lock=False)
            for item in items
        ]
        dem = merge_arrays(tiles) if len(tiles) > 1 else tiles[0]
        clipped = dem.rio.clip([geojson], crs="EPSG:4326", drop=True)

        band = clipped.values[0]
        row, col = np.unravel_index(int(np.nanargmax(band)), band.shape)

        return (
            GeoPoint(longitude=float(clipped.x[col]), latitude=float(clipped.y[row])),
            Elevation(meters=float(band[row, col])),
        )

    def get_point_elevation(self, point: GeoPoint) -> Elevation:
        items = self._find_items(point.to_geojson())
        da = rioxarray.open_rasterio(items[0].assets[_ASSET_KEY].href, masked=True, lock=False)
        value = float(da.sel(x=point.longitude, y=point.latitude, method="nearest").values[0])
        return Elevation(meters=value)
