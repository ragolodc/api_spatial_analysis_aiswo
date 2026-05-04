from types import SimpleNamespace
from uuid import uuid4

from src.modules.pivot_geometry_analysis.application.commands.run_slope_analysis import (
    RunSlopeAnalysis,
)
from src.modules.pivot_geometry_analysis.domain.entities import SlopeAnalysisJobRequest


class _DummySpansConfig:
    def get_radii_m(self) -> list[float]:
        return [10.0]


class _DummyProfileReader:
    def get_longitudinal_profiles(self, request_id):
        return []

    def get_transversal_profiles(self, request_id):
        return []

    def get_spans_configurations(self, request_id):
        return _DummySpansConfig()


def test_execute_with_critical_nodes_uses_internal_force_without_crashing():
    service = RunSlopeAnalysis(profile_reader=_DummyProfileReader())

    critical_node = SimpleNamespace(
        is_critical=True,
        azimuth_deg=10.0,
        tower_index=2,
        internal_force_kN=12.34,
        force_type="compression",
    )

    def _fake_run_analysis_chain(**kwargs):
        return {
            "longitudinal_slope_analysis": SimpleNamespace(),
            "transversal_slope_analysis": SimpleNamespace(),
            "torsional_slope_analysis": SimpleNamespace(),
            "structural_stress_analysis": SimpleNamespace(nodes=[critical_node]),
            "crop_clearance_analysis": SimpleNamespace(),
        }

    service._run_analysis_chain = _fake_run_analysis_chain

    request = SlopeAnalysisJobRequest(
        request_id=uuid4(),
        zone_id=uuid4(),
        profile_analysis_id=uuid4(),
        payload={"inputs": {}},
    )

    result = service.execute(request)

    assert result.request_id == request.request_id
