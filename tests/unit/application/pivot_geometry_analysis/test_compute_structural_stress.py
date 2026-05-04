from uuid import uuid4

import pytest

from src.modules.pivot_geometry_analysis.application.services.compute_structural_stress import (
    ComputeStructuralStress,
)
from src.modules.pivot_geometry_analysis.domain.entities import (
    LongitudinalSlopeAnalysis,
    NodeKind,
    RunKind,
    SpanSlopeResult,
)
from src.modules.pivot_geometry_analysis.domain.value_objects import SlopeValue, ThresholdConfig

CONFIG = ThresholdConfig(max_value=8.0)
SVC = ComputeStructuralStress()


def _slope(pct: float) -> SlopeValue:
    return SlopeValue.from_pct(pct)


def _longitudinal(azimuth: float, slopes: list[float]) -> LongitudinalSlopeAnalysis:
    radii = [i * 100.0 for i in range(len(slopes) + 1)]
    return LongitudinalSlopeAnalysis(
        request_id=uuid4(),
        spans=[
            SpanSlopeResult(
                azimuth_deg=azimuth,
                span_index=i,
                radius_start_m=radii[i],
                radius_end_m=radii[i + 1],
                slope=_slope(pct),
                classification="ok",
                service_weight=100.0,
            )
            for i, pct in enumerate(slopes)
        ],
    )


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def test_node_count():
    long = _longitudinal(0.0, [2.0, 3.0, 4.0])  # 3 spans → 4 nodes (pivote + 3 torres)
    result = SVC.execute(uuid4(), long, CONFIG)
    assert len(result.nodes) == 4


def test_valley_node():
    # span_in descends (-2 %) then span_out ascends (+3 %) → valley at inner node
    long = _longitudinal(0.0, [-2.0, 3.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert result.nodes[1].node_kind == NodeKind.VALLEY


def test_crest_node():
    # span_in ascends (+3 %) then span_out descends (-2 %) → crest at inner node
    long = _longitudinal(0.0, [3.0, -2.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert result.nodes[1].node_kind == NodeKind.CREST


def test_neutral_node():
    long = _longitudinal(0.0, [3.0, 3.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert result.nodes[0].node_kind == NodeKind.NEUTRAL


def test_delta_calculation():
    # delta = slope_out - slope_in = 5 - (-3) = 8 % at inner node
    long = _longitudinal(0.0, [-3.0, 5.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert result.nodes[1].delta.pct == pytest.approx(8.0)


def test_valley_double_check_triggered():
    # delta = 20 % > 2 × 8 % = 16 % → valley_double_check True at inner node
    long = _longitudinal(0.0, [-10.0, 10.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert result.nodes[1].valley_double_check is True


def test_valley_double_check_not_triggered():
    # delta = 6 % < 16 % at inner node
    long = _longitudinal(0.0, [-2.0, 4.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert result.nodes[1].valley_double_check is False


def test_node_classification_violation():
    # delta = 20 % > max(8 %) at inner node
    long = _longitudinal(0.0, [-10.0, 10.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert result.nodes[1].classification == "violation"


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


def test_no_run_for_single_span():
    long = _longitudinal(0.0, [-3.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert len(result.runs) == 0


def test_tension_run_descending():
    # two consecutive negative spans → tension run
    long = _longitudinal(0.0, [-3.0, -4.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert len(result.runs) == 1
    assert result.runs[0].run_kind == RunKind.TENSION


def test_compression_run_ascending():
    # two consecutive positive spans → compression run
    long = _longitudinal(0.0, [3.0, 4.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert len(result.runs) == 1
    assert result.runs[0].run_kind == RunKind.COMPRESSION


def test_cumulative_slope():
    long = _longitudinal(0.0, [-3.0, -4.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert result.runs[0].cumulative_slope_pct == pytest.approx(-7.0)


def test_run_span_indices():
    long = _longitudinal(0.0, [-3.0, -4.0, -2.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert result.runs[0].span_indices == [0, 1, 2]


def test_no_run_for_alternating_slopes():
    # slope alternates → no consecutive same-sign pair of length >= 2
    long = _longitudinal(0.0, [-3.0, 4.0, -2.0])
    result = SVC.execute(uuid4(), long, CONFIG)
    assert len(result.runs) == 0
