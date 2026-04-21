from dataclasses import dataclass

from src.shared.domain.value_objects import GeoPoint  # re-exported from shared kernel

__all__ = ["GeoPoint", "Elevation"]


@dataclass(frozen=True)
class Elevation:
    meters: float
