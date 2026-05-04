from uuid import uuid4

import pytest

from src.modules.pivot_geometry_analysis.application.services.compute_crop_clearance import (
    ComputeCropClearance,
)
from src.modules.pivot_geometry_analysis.domain.entities import (
    NodeKind,
    NodeStressResult,
    StructuralStressAnalysis,
)
from src.modules.pivot_geometry_analysis.domain.value_objects import SlopeValue
from src.modules.profile_analysis.domain.entities import LongitudinalProfile, ProfileSamplePoint

RADII = (100.0, 200.0)
H_BOOM = 3.0
CROP_RISK = 2.0
GROUND_RISK = 0.5
SVC = ComputeCropClearance()


def _slope(pct: float) -> SlopeValue:
    return SlopeValue.from_pct(pct)


def _profile(azimuth: float, pts: list[tuple[float, float | None]]) -> LongitudinalProfile:
    return LongitudinalProfile(
        azimuth_deg=azimuth,
        points=[
            ProfileSamplePoint(
                longitude=0.0,
                latitude=0.0,
                distance_m=r,
                radius_m=r,
                angle_deg=azimuth,
                elevation_m=z,
            )
            for r, z in pts
        ],
    )


def _empty_structural() -> StructuralStressAnalysis:
    return StructuralStressAnalysis(request_id=uuid4(), nodes=[], runs=[])


def _structural_with_valley(azimuth: float, tower_index: int) -> StructuralStressAnalysis:
    node = NodeStressResult(
        azimuth_deg=azimuth,
        tower_index=tower_index,
        radius_m=tower_index * 100.0,
        slope_in=_slope(-2.0),
        slope_out=_slope(2.0),
        delta=_slope(4.0),
        node_kind=NodeKind.VALLEY,
        classification="ok",
        valley_double_check=False,
        left_force_kN=0.0,
        right_force_kN=0.0,
        internal_force_kN=0.0,
        force_type="neutral",
        safety_factor=float("inf"),
        is_critical=False,
    )
    return StructuralStressAnalysis(request_id=uuid4(), nodes=[node], runs=[])


# ---------------------------------------------------------------------------
# Clearance calculation
# ---------------------------------------------------------------------------


def test_clearance_ok():
    # tower elevations: 0=10m, 100=10m, 200=10m; boom=3m; terrain midpoint=10m
    # boom at midpoint = 10 + 3 = 13; clearance = 13 - 10 = 3 > crop_risk(2)
    profile = _profile(
        0.0, [(0.0, 10.0), (50.0, 10.0), (100.0, 10.0), (150.0, 10.0), (200.0, 10.0)]
    )
    result = SVC.execute(
        uuid4(), [profile], RADII, H_BOOM, CROP_RISK, GROUND_RISK, _empty_structural()
    )
    interior = [p for p in result.points if p.distance_m not in (0.0, 100.0, 200.0)]
    assert all(p.classification == "ok" for p in interior)


def test_clearance_crop_risk():
    # terrain rises so clearance = 1.5 m → crop_risk (< 2 but > 0.5)
    # tower 0 at z=10, tower 1 at z=10 → boom interpolated = 13 everywhere
    # terrain at midpoint = 11.5 → clearance = 1.5
    profile = _profile(0.0, [(0.0, 10.0), (50.0, 11.5), (100.0, 10.0)])
    result = SVC.execute(
        uuid4(), [profile], (100.0,), H_BOOM, CROP_RISK, GROUND_RISK, _empty_structural()
    )
    mid = [p for p in result.points if p.distance_m == 50.0]
    assert mid[0].classification == "crop_risk"


def test_clearance_ground_risk():
    # terrain at midpoint = 12.8 → clearance = 0.2 < ground_risk(0.5)
    profile = _profile(0.0, [(0.0, 10.0), (50.0, 12.8), (100.0, 10.0)])
    result = SVC.execute(
        uuid4(), [profile], (100.0,), H_BOOM, CROP_RISK, GROUND_RISK, _empty_structural()
    )
    mid = [p for p in result.points if p.distance_m == 50.0]
    assert mid[0].classification == "ground_risk"


def test_boom_elevation_interpolated():
    # tower at r=0 z=10, tower at r=100 z=20 → at r=50, boom = (10+3)*0.5 + (20+3)*0.5 = 18
    profile = _profile(0.0, [(0.0, 10.0), (50.0, 5.0), (100.0, 20.0)])
    result = SVC.execute(
        uuid4(), [profile], (100.0,), H_BOOM, CROP_RISK, GROUND_RISK, _empty_structural()
    )
    mid = [p for p in result.points if p.distance_m == 50.0]
    assert mid[0].boom_elevation_m == pytest.approx(18.0)


def test_clearance_value():
    # boom = 18.0, terrain = 5.0 → clearance = 13.0
    profile = _profile(0.0, [(0.0, 10.0), (50.0, 5.0), (100.0, 20.0)])
    result = SVC.execute(
        uuid4(), [profile], (100.0,), H_BOOM, CROP_RISK, GROUND_RISK, _empty_structural()
    )
    mid = [p for p in result.points if p.distance_m == 50.0]
    assert mid[0].clearance_m == pytest.approx(13.0)


# ---------------------------------------------------------------------------
# in_valley_node
# ---------------------------------------------------------------------------


def test_in_valley_node_true_when_valley_at_span_start():
    # node at tower_index=1 (= end of span 0) → span 0 has in_valley_node=True
    profile = _profile(0.0, [(0.0, 10.0), (50.0, 10.0), (100.0, 10.0)])
    structural = _structural_with_valley(azimuth=0.0, tower_index=1)
    result = SVC.execute(uuid4(), [profile], (100.0,), H_BOOM, CROP_RISK, GROUND_RISK, structural)
    interior = [p for p in result.points if p.distance_m == 50.0]
    assert interior[0].in_valley_node is True


def test_in_valley_node_false_when_no_valley():
    profile = _profile(0.0, [(0.0, 10.0), (50.0, 10.0), (100.0, 10.0)])
    result = SVC.execute(
        uuid4(), [profile], (100.0,), H_BOOM, CROP_RISK, GROUND_RISK, _empty_structural()
    )
    assert all(not p.in_valley_node for p in result.points)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_missing_elevation_skipped():
    profile = _profile(0.0, [(0.0, 10.0), (50.0, None), (100.0, 10.0)])
    result = SVC.execute(
        uuid4(), [profile], (100.0,), H_BOOM, CROP_RISK, GROUND_RISK, _empty_structural()
    )
    distances = [p.distance_m for p in result.points]
    assert 50.0 not in distances


def test_point_outside_radii_skipped():
    # point at r=150 is outside radii (0..100)
    profile = _profile(0.0, [(0.0, 10.0), (100.0, 10.0), (150.0, 10.0)])
    result = SVC.execute(
        uuid4(), [profile], (100.0,), H_BOOM, CROP_RISK, GROUND_RISK, _empty_structural()
    )
    distances = [p.distance_m for p in result.points]
    assert 150.0 not in distances
