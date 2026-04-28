"""Shared domain entities used across all bounded contexts."""

from dataclasses import dataclass
from datetime import datetime
from itertools import accumulate
from uuid import UUID


@dataclass(slots=True)
class ElevationSource:
    """Configured elevation data source. Shared across all bounded contexts that use DEM data."""

    id: UUID
    name: str
    srid: int
    source_url: str | None
    collection: str | None
    resolution_m: float
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class Spans:
    position: int
    length: float
    dry_weight: float
    service_weight: float


class SpansConfig:
    def __init__(self, spans: list[Spans]):
        if spans is None or len(spans) <= 0:
            raise ValueError("The spans list can't be empty")
        self._spans = spans

    def get_radii_m(self):
        # Ordena los spans por posición y luego extrae las longitudes
        sorted_spans = sorted(self._spans, key=lambda span: span.position)
        return list(accumulate(span.length for span in sorted_spans))

    def get_span_by_radius(self, radius_m: float) -> Spans:
        for span in self._spans:
            if span.length == radius_m:
                return span
        raise ValueError(f"No span found for radius {radius_m}")

    def get_span_by_position(self, position: int) -> Spans:
        for span in self._spans:
            if span.position == position:
                return span
        raise ValueError(f"No span found for position {position}")
