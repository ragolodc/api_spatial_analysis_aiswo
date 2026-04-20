from typing import Any

import planetary_computer
import pystac_client
import rioxarray  # noqa: F401
from rioxarray.merge import merge_arrays

_ASSET_KEY = "data"
_CLIP_CRS = "EPSG:4326"
_DEFAULT_MAX_TILES = 16


def fetch_dem_tiles(
    catalog_url: str, collection: str, geometry: dict[str, Any], max_tiles: int = _DEFAULT_MAX_TILES
):
    """Busca y abre tiles DEM desde un catálogo STAC para una geometría dada."""
    catalog = pystac_client.Client.open(catalog_url, modifier=planetary_computer.sign_inplace)
    items = list(
        catalog.search(collections=[collection], intersects=geometry, max_items=max_tiles).items()
    )
    return [
        rioxarray.open_rasterio(item.assets[_ASSET_KEY].href, masked=True, lock=False)
        for item in items
    ]


def merge_dem_tiles(tiles: list):
    """Combina múltiples tiles DEM en un único array."""
    return merge_arrays(tiles) if len(tiles) > 1 else tiles[0]


def clip_dem(dem, geometry: dict[str, Any], crs: str = _CLIP_CRS):
    """Recorta el DEM a la geometría dada."""
    return dem.rio.clip([geometry], crs=crs, drop=True)
