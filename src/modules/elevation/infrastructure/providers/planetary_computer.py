from uuid import UUID

import numpy as np
import rioxarray  # noqa: F401  — registers .rio accessor on xarray DataArray

from src.modules.elevation.domain.exceptions import ElevationDataNotFound
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint
from src.shared.domain import GeoPolygon
from src.shared.domain.exceptions import DemNotAvailable
from src.shared.infrastructure.dem.stac_dem_loader import clip_dem, fetch_dem_tiles, merge_dem_tiles


class PlanetaryComputerElevationProvider:
    def __init__(self, catalog_url: str, collection: str, source_id: UUID) -> None:
        self._catalog_url = catalog_url
        self._collection = collection
        self._source_id = source_id

    def get_highest_point(self, polygon: GeoPolygon) -> tuple[GeoPoint, Elevation]:
        geojson = polygon.to_geojson()
        tiles = fetch_dem_tiles(self._catalog_url, self._collection, geojson)
        if not tiles:
            raise ElevationDataNotFound("No DEM coverage found for the given geometry")
        dem = merge_dem_tiles(tiles)
        clipped = clip_dem(dem, geojson)

        try:
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

        tiles = fetch_dem_tiles(self._catalog_url, self._collection, point.to_geojson())
        if not tiles:
            raise ElevationDataNotFound("No DEM coverage found for the requested point")

        da = tiles[0]
        try:
            value = float(da.sel(x=point.longitude, y=point.latitude, method="nearest").values[0])
            if np.isnan(value):
                raise ElevationDataNotFound("DEM value at point is nodata")
            return Elevation(meters=value)
        finally:
            for tile in tiles:
                tile.close()
