from uuid import UUID

import numpy as np
import rioxarray  # noqa: F401 — registers .rio accessor
from contourpy import contour_generator
from shapely.geometry import MultiLineString, mapping, shape

from src.modules.elevation_analysis.domain.entities import PointType
from src.modules.elevation_analysis.domain.exceptions import DemNotAvailable
from src.shared.domain import GeoPolygon
from src.shared.infrastructure.dem.stac_dem_loader import clip_dem, fetch_dem_tiles, merge_dem_tiles

_PROVIDER_NAME = "planetary_computer"


class PlanetaryComputerAnalysisProvider:
    """
    Proveedor de análisis de elevación usando Copernicus DEM 30m
    desde Microsoft Planetary Computer.
    """

    def __init__(self, catalog_url: str, collection: str, source_id: UUID) -> None:
        self._catalog_url = catalog_url
        self._collection = collection
        self._source_id = source_id

    @property
    def name(self) -> str:
        return _PROVIDER_NAME

    @property
    def source_id(self) -> UUID:
        return self._source_id

    def _fetch_clipped_dem(self, polygon: GeoPolygon):
        """Descarga y recorta los tiles DEM que cubren el polígono."""
        geojson = polygon.to_geojson()
        tiles = fetch_dem_tiles(self._catalog_url, self._collection, geojson)
        if not tiles:
            raise DemNotAvailable("No DEM coverage found for the given geometry")
        dem = merge_dem_tiles(tiles)
        clipped = clip_dem(dem, geojson)
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
            results.append(
                (
                    PointType.HIGHEST,
                    float(clipped.x[col_hi]),
                    float(clipped.y[row_hi]),
                    highest,
                )
            )

            row_lo, col_lo = np.unravel_index(int(np.nanargmin(band)), band.shape)
            lowest = float(band[row_lo, col_lo])
            if np.isnan(lowest):
                raise DemNotAvailable("Unable to determine lowest elevation")
            results.append(
                (
                    PointType.LOWEST,
                    float(clipped.x[col_lo]),
                    float(clipped.y[row_lo]),
                    lowest,
                )
            )

            poly_shape = shape(polygon.to_geojson())
            centroid = poly_shape.centroid
            elev_centroid = float(
                clipped.sel(x=centroid.x, y=centroid.y, method="nearest").values[0]
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

    def get_contours(self, polygon: GeoPolygon, interval_m: float) -> list[tuple[float, dict]]:
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
