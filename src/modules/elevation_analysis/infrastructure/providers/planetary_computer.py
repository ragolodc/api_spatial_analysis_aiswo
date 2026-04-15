import numpy as np
import planetary_computer
import pystac_client
import rioxarray  # noqa: F401 — registers .rio accessor
from contourpy import contour_generator
from rioxarray.merge import merge_arrays
from shapely.geometry import MultiLineString, mapping, shape

from src.modules.elevation.domain.exceptions import ElevationDataNotFound
from src.modules.elevation.domain.value_objects import GeoPolygon
from src.modules.elevation_analysis.domain.entities import PointType

_CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
_COLLECTION = "cop-dem-glo-30"
_ASSET_KEY = "data"


class PlanetaryComputerAnalysisProvider:
    """
    Proveedor de análisis de elevación usando Copernicus DEM 30m
    desde Microsoft Planetary Computer.
    """

    def _fetch_clipped_dem(self, polygon: GeoPolygon):
        """Descarga y recorta los tiles DEM que cubren el polígono."""
        geojson = polygon.to_geojson()
        catalog = pystac_client.Client.open(
            _CATALOG_URL, modifier=planetary_computer.sign_inplace
        )
        items = list(
            catalog.search(
                collections=[_COLLECTION], intersects=geojson, max_items=16
            ).items()
        )
        if not items:
            raise ElevationDataNotFound("No DEM coverage found for the given geometry")

        tiles = [
            rioxarray.open_rasterio(item.assets[_ASSET_KEY].href, masked=True, lock=False)
            for item in items
        ]
        dem = merge_arrays(tiles) if len(tiles) > 1 else tiles[0]
        return dem.rio.clip([geojson], crs="EPSG:4326", drop=True)

    def get_characteristic_points(
        self, polygon: GeoPolygon
    ) -> list[tuple[PointType, float, float, float]]:
        """
        Devuelve los tres puntos característicos del DEM dentro del polígono:
        más alto, más bajo y centroide.
        """
        clipped = self._fetch_clipped_dem(polygon)
        band = clipped.values[0]

        results = []

        # Punto más alto
        row_hi, col_hi = np.unravel_index(int(np.nanargmax(band)), band.shape)
        results.append((
            PointType.HIGHEST,
            float(clipped.x[col_hi]),
            float(clipped.y[row_hi]),
            float(band[row_hi, col_hi]),
        ))

        # Punto más bajo
        row_lo, col_lo = np.unravel_index(int(np.nanargmin(band)), band.shape)
        results.append((
            PointType.LOWEST,
            float(clipped.x[col_lo]),
            float(clipped.y[row_lo]),
            float(band[row_lo, col_lo]),
        ))

        # Centroide: muestreo de elevación en el centro geométrico del polígono
        poly_shape = shape(polygon.to_geojson())
        centroid = poly_shape.centroid
        elev_centroid = float(
            clipped.sel(
                x=centroid.x, y=centroid.y, method="nearest"
            ).values[0]
        )
        results.append((PointType.CENTROID, centroid.x, centroid.y, elev_centroid))

        return results

    def get_contours(
        self, polygon: GeoPolygon, interval_m: float
    ) -> list[tuple[float, dict]]:
        """
        Genera curvas de nivel del DEM recortado al polígono.
        Devuelve [(elevation_m, geojson_multilinestring), ...] por cada nivel.
        """
        clipped = self._fetch_clipped_dem(polygon)
        band = clipped.values[0].astype(float)

        x = clipped.x.values  # longitudes (1D)
        y = clipped.y.values  # latitudes  (1D, decreciente)

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
            # Filtrar líneas con menos de 2 puntos (inválidas)
            valid = [line for line in lines if len(line) >= 2]
            if not valid:
                continue
            ml = MultiLineString([line.tolist() for line in valid])
            result.append((float(level), mapping(ml)))

        return result
