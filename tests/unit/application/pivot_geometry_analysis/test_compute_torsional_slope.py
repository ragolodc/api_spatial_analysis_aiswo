from uuid import uuid4

import pytest

from src.modules.pivot_geometry_analysis.application.services.compute_torsional_slope import (
    ComputeTorsionalSlope,
)
from src.modules.pivot_geometry_analysis.domain.entities import (
    LongitudinalSlopeAnalysis,
    SpanSlopeResult,
    TransversalSlopeAnalysis,
    TransversalSlopePoint,
)
from src.modules.pivot_geometry_analysis.domain.value_objects import SlopeValue, ThresholdConfig

TORSION_CONFIG = ThresholdConfig(max_value=6.0)
LONG_CONFIG = ThresholdConfig(max_value=8.0)
SVC = ComputeTorsionalSlope()


def _slope(pct: float) -> SlopeValue:
    return SlopeValue.from_pct(pct)


def _longitudinal(
    azimuth: float, spans: list[tuple[int, float, float, float]]
) -> LongitudinalSlopeAnalysis:
    """spans = [(span_index, r_start, r_end, slope_pct), ...]"""
    return LongitudinalSlopeAnalysis(
        request_id=uuid4(),
        spans=[
            SpanSlopeResult(
                azimuth_deg=azimuth,
                span_index=idx,
                radius_start_m=r_start,
                radius_end_m=r_end,
                slope=_slope(pct),
                classification="ok",
                service_weight=0.0,
            )
            for idx, r_start, r_end, pct in spans
        ],
    )


def _transversal(pts: list[tuple[float, float, float, float]]) -> TransversalSlopeAnalysis:
    """pts = [(radius_m, az_from, az_to, slope_pct), ...]"""
    return TransversalSlopeAnalysis(
        request_id=uuid4(),
        points=[
            TransversalSlopePoint(
                radius_m=r,
                azimuth_from_deg=az_from,
                azimuth_to_deg=az_to,
                arc_length_m=10.0,
                slope=_slope(pct),
                classification="ok",
            )
            for r, az_from, az_to, pct in pts
        ],
    )


def test_torsion_zero_when_same_slope():
    long = _longitudinal(5.0, [(0, 0.0, 100.0, 2.0)])
    trans = _transversal(
        [
            (0.0, 0.0, 10.0, 3.0),
            (100.0, 0.0, 10.0, 3.0),
        ]
    )
    result = SVC.execute(uuid4(), long, trans, TORSION_CONFIG, LONG_CONFIG)
    assert len(result.spans) == 1
    assert result.spans[0].torsion.pct == pytest.approx(0.0)


def test_torsion_positive():
    long = _longitudinal(5.0, [(0, 0.0, 100.0, 2.0)])
    trans = _transversal(
        [
            (0.0, 0.0, 10.0, 1.0),
            (100.0, 0.0, 10.0, 4.0),
        ]
    )
    result = SVC.execute(uuid4(), long, trans, TORSION_CONFIG, LONG_CONFIG)
    assert result.spans[0].torsion.pct == pytest.approx(3.0)  # 4 - 1


def test_torsion_negative():
    long = _longitudinal(5.0, [(0, 0.0, 100.0, 2.0)])
    trans = _transversal(
        [
            (0.0, 0.0, 10.0, 5.0),
            (100.0, 0.0, 10.0, 2.0),
        ]
    )
    result = SVC.execute(uuid4(), long, trans, TORSION_CONFIG, LONG_CONFIG)
    assert result.spans[0].torsion.pct == pytest.approx(-3.0)  # 2 - 5


def test_combined_load_index():
    # torsion=3%, long=2%, limits=6 and 8 → combined = 3/6 + 2/8 = 0.5 + 0.25 = 0.75
    long = _longitudinal(5.0, [(0, 0.0, 100.0, 2.0)])
    trans = _transversal(
        [
            (0.0, 0.0, 10.0, 0.0),
            (100.0, 0.0, 10.0, 3.0),
        ]
    )
    result = SVC.execute(uuid4(), long, trans, TORSION_CONFIG, LONG_CONFIG)
    assert result.spans[0].combined_load_index == pytest.approx(0.75)


def test_missing_transversal_skips_span():
    long = _longitudinal(5.0, [(0, 0.0, 100.0, 2.0)])
    # transversal only covers azimuth 90-100, not 5 degrees
    trans = _transversal(
        [
            (0.0, 90.0, 100.0, 1.0),
            (100.0, 90.0, 100.0, 3.0),
        ]
    )
    result = SVC.execute(uuid4(), long, trans, TORSION_CONFIG, LONG_CONFIG)
    assert len(result.spans) == 0


def test_classification_violation():
    # torsion = 7 % > max(6 %)
    long = _longitudinal(5.0, [(0, 0.0, 100.0, 1.0)])
    trans = _transversal(
        [
            (0.0, 0.0, 10.0, 0.0),
            (100.0, 0.0, 10.0, 7.0),
        ]
    )
    result = SVC.execute(uuid4(), long, trans, TORSION_CONFIG, LONG_CONFIG)
    assert result.spans[0].classification == "violation"


def test_longitudinal_slope_preserved():
    long = _longitudinal(5.0, [(0, 0.0, 100.0, 4.5)])
    trans = _transversal(
        [
            (0.0, 0.0, 10.0, 1.0),
            (100.0, 0.0, 10.0, 2.0),
        ]
    )
    result = SVC.execute(uuid4(), long, trans, TORSION_CONFIG, LONG_CONFIG)
    assert result.spans[0].longitudinal_slope.pct == pytest.approx(4.5)
