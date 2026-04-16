import numpy as np
import planetary_computer
import pystac_client
import rioxarray  # noqa: F401  — registers .rio accessor on xarray DataArray
from rioxarray.merge import merge_arrays

from src.modules.elevation.domain.exceptions import ElevationDataNotFound
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint
from src.shared.domain import GeoPolygon

_ASSET_KEY = "data"
_CLIP_CRS = "EPSG:4326"
_MAX_DEM_TILES = 16


class PlanetaryComputerElevationProvider:

    def __init__(self, catalog_url: str, collection: str) -> None:
        self._catalog_url = catalog_url
        self._collection = collection

    def _find_items(self, geometry: dict) -> list:
        catalog = pystac_client.Client.open(
            self._catalog_url, modifier=planetary_computer.sign_inplace
        )
        items = list(
            catalog.search(
                collections=[self._collection], intersects=geometry, max_items=_MAX_DEM_TILES
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
        dem = None
        clipped = None
        try:
            dem = merge_arrays(tiles) if len(tiles) > 1 else tiles[0]
            clipped = dem.rio.clip([geojson], crs=_CLIP_CRS, drop=True)

            band = clipped.values[0]
            if np.isnan(band).all():
                raise ElevationDataNotFound("DEM tiles for polygon only contain nodata values")

            row, col = np.unravel_index(int(np.nanargmax(band)), band.shape)
            highest = float(band[row, col])
            if np.isnan(highest):
                raise ElevationDataNotFound("Unable to determine highest point elevation")

            return (
                GeoPoint(longitude=float(clipped.x[col]), latitude=float(clipped.y[row])),
                Elevation(meters=highest),
            )
        finally:
            if clipped is not None:
                clipped.close()
            if dem is not None and not any(dem is tile for tile in tiles):
                dem.close()
            for tile in tiles:
                tile.close()

    def get_point_elevation(self, point: GeoPoint) -> Elevation:
        items = self._find_items(point.to_geojson())
        da = rioxarray.open_rasterio(items[0].assets[_ASSET_KEY].href, masked=True, lock=False)
        try:
            value = float(da.sel(x=point.longitude, y=point.latitude, method="nearest").values[0])
            if np.isnan(value):
                raise ElevationDataNotFound("DEM value at point is nodata")
            return Elevation(meters=value)
        finally:
            da.close()
