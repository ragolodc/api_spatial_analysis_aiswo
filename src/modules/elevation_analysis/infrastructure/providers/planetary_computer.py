import numpy as np
import planetary_computer
import pystac_client
import rioxarray  # noqa: F401 — registers .rio accessor
from contourpy import contour_generator
from rioxarray.merge import merge_arrays
from shapely.geometry import MultiLineString, mapping, shape

from src.modules.elevation_analysis.domain.entities import PointType
from src.modules.elevation_analysis.domain.exceptions import DemNotAvailable
from src.shared.domain import GeoPolygon

_ASSET_KEY = "data"
_PROVIDER_NAME = "planetary_computer"
_RESOLUTION_M = 30.0
_MAX_DEM_TILES = 16
_CLIP_CRS = "EPSG:4326"


class PlanetaryComputerAnalysisProvider:
    """
    Proveedor de análisis de elevación usando Copernicus DEM 30m
    desde Microsoft Planetary Computer.
    """

    def __init__(self, catalog_url: str, collection: str) -> None:
        self._catalog_url = catalog_url
        self._collection = collection

    @property
    def name(self) -> str:
        return _PROVIDER_NAME

    @property
    def resolution_m(self) -> float:
        return _RESOLUTION_M

    def _fetch_clipped_dem(self, polygon: GeoPolygon):
        """Descarga y recorta los tiles DEM que cubren el polígono."""
        geojson = polygon.to_geojson()
        catalog = pystac_client.Client.open(
            self._catalog_url, modifier=planetary_computer.sign_inplace
        )
        items = list(
            catalog.search(
                collections=[self._collection], intersects=geojson, max_items=_MAX_DEM_TILES
            ).items()
        )
        if not items:
            raise DemNotAvailable("No DEM coverage found for the given geometry")

        tiles = [
            rioxarray.open_rasterio(item.assets[_ASSET_KEY].href, masked=True, lock=False)
            for item in items
        ]
        dem = merge_arrays(tiles) if len(tiles) > 1 else tiles[0]
        clipped = dem.rio.clip([geojson], crs=_CLIP_CRS, drop=True)
        return clipped, dem, tiles

    def get_characteristic_points(
        self, polygon: GeoPolygon
    ) -> list[tuple[PointType, float, float, float]]:
        """
        Devuelve los tres puntos característicos del DEM dentro del polígono:
        más alto, más bajo y centroide.
        """
        clipped, dem, tiles = self._fetch_clipped_dem(polygon)
        try:
            band = clipped.values[0]
            if np.isnan(band).all():
                raise DemNotAvailable("DEM tiles for polygon only contain nodata values")

            results = []

            row_hi, col_hi = np.unravel_index(int(np.nanargmax(band)), band.shape)
            highest = float(band[row_hi, col_hi])
            if np.isnan(highest):
                raise DemNotAvailable("Unable to determine highest elevation")
            results.append((
                PointType.HIGHEST,
                float(clipped.x[col_hi]),
                float(clipped.y[row_hi]),
                highest,
            ))

            row_lo, col_lo = np.unravel_index(int(np.nanargmin(band)), band.shape)
            lowest = float(band[row_lo, col_lo])
            if np.isnan(lowest):
                raise DemNotAvailable("Unable to determine lowest elevation")
            results.append((
                PointType.LOWEST,
                float(clipped.x[col_lo]),
                float(clipped.y[row_lo]),
                lowest,
            ))

            poly_shape = shape(polygon.to_geojson())
            centroid = poly_shape.centroid
            elev_centroid = float(
                clipped.sel(
                    x=centroid.x, y=centroid.y, method="nearest"
                ).values[0]
            )
            if np.isnan(elev_centroid):
                raise DemNotAvailable("Unable to determine centroid elevation")
            results.append((PointType.CENTROID, centroid.x, centroid.y, elev_centroid))

            return results
        finally:
            clipped.close()
            if not any(dem is tile for tile in tiles):
                dem.close()
            for tile in tiles:
                tile.close()

    def get_contours(
        self, polygon: GeoPolygon, interval_m: float
    ) -> list[tuple[float, dict]]:
        """
        Genera curvas de nivel del DEM recortado al polígono.
        Devuelve [(elevation_m, geojson_multilinestring), ...] por cada nivel.
        """
        clipped, dem, tiles = self._fetch_clipped_dem(polygon)
        try:
            band = clipped.values[0].astype(float)
            if np.isnan(band).all():
                raise DemNotAvailable("DEM tiles for polygon only contain nodata values")

            x = clipped.x.values
            y = clipped.y.values

            z_min = float(np.nanmin(band))
            z_max = float(np.nanmax(band))

            if z_max - z_min < interval_m:
                return []

            levels = np.arange(
                np.ceil(z_min / interval_m) * interval_m,
                z_max,
                interval_m,
            )

            cg = contour_generator(x=x, y=y, z=band)
            result = []

            for level in levels:
                lines = cg.lines(float(level))
                if not lines:
                    continue
                valid = [line for line in lines if len(line) >= 2]
                if not valid:
                    continue
                ml = MultiLineString([line.tolist() for line in valid])
                result.append((float(level), mapping(ml)))

            return result
        finally:
            clipped.close()
            if not any(dem is tile for tile in tiles):
                dem.close()
            for tile in tiles:
                tile.close()
