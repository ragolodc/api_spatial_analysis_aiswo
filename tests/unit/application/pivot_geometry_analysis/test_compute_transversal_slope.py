import math
from uuid import uuid4

import pytest

from src.modules.pivot_geometry_analysis.application.services.compute_transversal_slope import (
    ComputeTransversalSlope,
)
from src.modules.pivot_geometry_analysis.domain.value_objects import ThresholdConfig
from src.modules.profile_analysis.domain.entities import ProfileSamplePoint, TransverseProfile

CONFIG = ThresholdConfig(max_value=8.0)
SVC = ComputeTransversalSlope()


def _profile(radius: float, pts: list[tuple[float, float | None]]) -> TransverseProfile:
    """pts = [(angle_deg, elevation_m), ...]"""
    return TransverseProfile(
        radius_m=radius,
        points=[
            ProfileSamplePoint(
                longitude=0.0,
                latitude=0.0,
                distance_m=radius,
                radius_m=radius,
                angle_deg=angle,
                elevation_m=z,
            )
            for angle, z in pts
        ],
    )


def test_arc_count():
    profile = _profile(100.0, [(0.0, 10.0), (10.0, 10.0), (20.0, 10.0)])
    result = SVC.execute(uuid4(), [profile], CONFIG)
    assert len(result.points) == 2


def test_flat_arc_slope_is_zero():
    profile = _profile(100.0, [(0.0, 10.0), (10.0, 10.0)])
    result = SVC.execute(uuid4(), [profile], CONFIG)
    assert result.points[0].slope.pct == pytest.approx(0.0)


def test_arc_length_matches_formula():
    # arc_length = r * delta_angle_rad
    r = 100.0
    d_angle_deg = 5.0
    expected = r * math.radians(d_angle_deg)
    profile = _profile(r, [(0.0, 0.0), (d_angle_deg, 0.0)])
    result = SVC.execute(uuid4(), [profile], CONFIG)
    assert result.points[0].arc_length_m == pytest.approx(expected)


def test_positive_slope():
    r = 100.0
    d_angle_deg = 5.0
    dx = r * math.radians(d_angle_deg)
    dz = 3.0
    expected_pct = (dz / dx) * 100.0
    profile = _profile(r, [(0.0, 0.0), (d_angle_deg, dz)])
    result = SVC.execute(uuid4(), [profile], CONFIG)
    assert result.points[0].slope.pct == pytest.approx(expected_pct)


def test_missing_elevation_skips_arc():
    profile = _profile(100.0, [(0.0, None), (10.0, 5.0), (20.0, 5.0)])
    result = SVC.execute(uuid4(), [profile], CONFIG)
    assert len(result.points) == 1  # only second arc (10→20) is valid


def test_classification_violation():
    r = 100.0
    d_angle_deg = 1.0
    dx = r * math.radians(d_angle_deg)
    # 10 % slope → violation (max 8 %)
    dz = dx * 0.10
    profile = _profile(r, [(0.0, 0.0), (d_angle_deg, dz)])
    result = SVC.execute(uuid4(), [profile], CONFIG)
    assert result.points[0].classification == "violation"


def test_azimuth_from_to_are_set():
    profile = _profile(100.0, [(30.0, 0.0), (40.0, 0.0)])
    result = SVC.execute(uuid4(), [profile], CONFIG)
    assert result.points[0].azimuth_from_deg == pytest.approx(30.0)
    assert result.points[0].azimuth_to_deg == pytest.approx(40.0)


def test_radius_is_preserved():
    profile = _profile(250.0, [(0.0, 0.0), (5.0, 0.0)])
    result = SVC.execute(uuid4(), [profile], CONFIG)
    assert result.points[0].radius_m == pytest.approx(250.0)
