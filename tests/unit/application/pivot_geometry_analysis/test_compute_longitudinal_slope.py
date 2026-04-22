from uuid import uuid4

import pytest

from src.modules.pivot_geometry_analysis.application.services.compute_longitudinal_slope import (
    ComputeLongitudinalSlope,
)
from src.modules.pivot_geometry_analysis.domain.value_objects import ThresholdConfig
from src.modules.profile_analysis.domain.entities import LongitudinalProfile, ProfileSamplePoint

RADII = (100.0, 200.0, 300.0)
CONFIG = ThresholdConfig(max_value=8.0)
SVC = ComputeLongitudinalSlope()


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


def test_span_count():
    profile = _profile(0.0, [(0.0, 0.0), (100.0, 1.0), (200.0, 2.0), (300.0, 3.0)])
    result = SVC.execute(uuid4(), [profile], RADII, CONFIG)
    assert len(result.spans) == 3


def test_flat_slope_is_zero():
    profile = _profile(0.0, [(0.0, 10.0), (100.0, 10.0), (200.0, 10.0), (300.0, 10.0)])
    result = SVC.execute(uuid4(), [profile], RADII, CONFIG)
    assert all(s.slope.pct == pytest.approx(0.0) for s in result.spans)


def test_positive_slope():
    # +5 m over 100 m → 5 %
    profile = _profile(0.0, [(0.0, 0.0), (100.0, 5.0), (200.0, 10.0), (300.0, 15.0)])
    result = SVC.execute(uuid4(), [profile], RADII, CONFIG)
    assert all(s.slope.pct == pytest.approx(5.0) for s in result.spans)


def test_negative_slope():
    # -3 m over 100 m → -3 %
    profile = _profile(0.0, [(0.0, 9.0), (100.0, 6.0), (200.0, 3.0), (300.0, 0.0)])
    result = SVC.execute(uuid4(), [profile], RADII, CONFIG)
    assert all(s.slope.pct == pytest.approx(-3.0) for s in result.spans)


def test_classification_ok():
    profile = _profile(0.0, [(0.0, 0.0), (100.0, 5.0), (200.0, 10.0), (300.0, 15.0)])
    result = SVC.execute(uuid4(), [profile], RADII, CONFIG)
    assert all(s.classification == "ok" for s in result.spans)


def test_classification_violation():
    # 10 % > max_value(8 %)
    profile = _profile(0.0, [(0.0, 0.0), (100.0, 10.0), (200.0, 20.0), (300.0, 30.0)])
    result = SVC.execute(uuid4(), [profile], RADII, CONFIG)
    assert all(s.classification == "violation" for s in result.spans)


def test_missing_elevation_skips_span():
    profile = _profile(0.0, [(0.0, 0.0), (100.0, None), (200.0, 5.0), (300.0, 10.0)])
    result = SVC.execute(uuid4(), [profile], RADII, CONFIG)
    # spans that touch the None point are skipped
    assert len(result.spans) < 3


def test_span_radii_are_correct():
    profile = _profile(90.0, [(0.0, 0.0), (100.0, 1.0), (200.0, 2.0), (300.0, 3.0)])
    result = SVC.execute(uuid4(), [profile], RADII, CONFIG)
    assert result.spans[0].radius_start_m == pytest.approx(0.0)
    assert result.spans[0].radius_end_m == pytest.approx(100.0)
    assert result.spans[2].radius_start_m == pytest.approx(200.0)
    assert result.spans[2].radius_end_m == pytest.approx(300.0)


def test_multiple_azimuths():
    profiles = [
        _profile(0.0, [(0.0, 0.0), (100.0, 1.0), (200.0, 2.0), (300.0, 3.0)]),
        _profile(90.0, [(0.0, 0.0), (100.0, 2.0), (200.0, 4.0), (300.0, 6.0)]),
    ]
    result = SVC.execute(uuid4(), profiles, RADII, CONFIG)
    assert len(result.spans) == 6
