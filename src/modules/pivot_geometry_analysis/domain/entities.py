from dataclasses import dataclass
from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.value_objects import SlopeValue

# ---------------------------------------------------------------------------
# Longitudinal Slope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpanSlopeResult:
    """Slope of a single span at a single azimuth."""

    azimuth_deg: float
    span_index: int  # 0 = pivot-point → tower-1, 1 = tower-1 → tower-2, …
    radius_start_m: float  # r of the inner tower (0.0 for the pivot point)
    radius_end_m: float  # r of the outer tower
    slope: SlopeValue
    classification: str


@dataclass(frozen=True)
class LongitudinalSlopeAnalysis:
    request_id: UUID
    spans: list[SpanSlopeResult]


# ---------------------------------------------------------------------------
# Transversal Slope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransversalSlopePoint:
    """Slope between two consecutive points on a transversal arc at radius r_i."""

    radius_m: float
    azimuth_from_deg: float
    azimuth_to_deg: float
    arc_length_m: float
    slope: SlopeValue
    classification: str


@dataclass(frozen=True)
class TransversalSlopeAnalysis:
    request_id: UUID
    points: list[TransversalSlopePoint]


# ---------------------------------------------------------------------------
# Crop Clearance
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClearancePoint:
    azimuth_deg: float
    distance_m: float  # distance along the radial from pivot center
    boom_elevation_m: float
    terrain_elevation_m: float
    clearance_m: float
    classification: str  # "ok" | "crop_risk" | "ground_risk"
    in_valley_node: bool  # True when this point is in a concave (valley) span


@dataclass(frozen=True)
class CropClearanceAnalysis:
    request_id: UUID
    points: list[ClearancePoint]


# ---------------------------------------------------------------------------
# Torsional Slope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TorsionalSlopeResult:
    """Torsion acting on a single span."""

    azimuth_deg: float
    span_index: int
    radius_start_m: float
    radius_end_m: float
    alpha_inner: SlopeValue  # transversal slope at inner tower
    alpha_outer: SlopeValue  # transversal slope at outer tower
    torsion: SlopeValue  # α_outer − α_inner  (signed)
    longitudinal_slope: SlopeValue  # from LongitudinalSlopeAnalysis
    combined_load_index: float  # |torsion|/t_limit + |long_slope|/l_limit
    classification: str  # based on |torsion| vs torsion_limit


@dataclass(frozen=True)
class TorsionalSlopeAnalysis:
    request_id: UUID
    spans: list[TorsionalSlopeResult]


# ---------------------------------------------------------------------------
# Structural Stress
# ---------------------------------------------------------------------------


class NodeKind:
    VALLEY = "valley"  # δ > 0  (concave — boom bends upward)
    CREST = "crest"  # δ < 0  (convex — boom bends downward)
    NEUTRAL = "neutral"  # δ == 0


class RunKind:
    TENSION = "tension"
    COMPRESSION = "compression"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class NodeStressResult:
    """Structural condition at each tower node (between two consecutive spans)."""

    azimuth_deg: float
    tower_index: int  # index in the radii array (0 = first tower)
    radius_m: float
    slope_in: SlopeValue  # slope of the span arriving at this tower
    slope_out: SlopeValue  # slope of the span leaving this tower
    delta: SlopeValue  # slope_out − slope_in  (signed, pct & deg)
    node_kind: str  # NodeKind constant
    classification: str  # based on |delta| vs limit; valleys also checked vs 2×limit
    valley_double_check: bool  # True when valley and |delta| > 2 × longitudinal_limit


@dataclass(frozen=True)
class StressRunResult:
    """A consecutive sequence of spans all under tension or compression."""

    azimuth_deg: float
    run_kind: str  # "tension" (descending) or "compression" (ascending)
    span_indices: list[int]
    cumulative_slope_pct: float


@dataclass(frozen=True)
class StructuralStressAnalysis:
    request_id: UUID
    nodes: list[NodeStressResult]
    runs: list[StressRunResult]
