"""Tests for slope analysis endpoints."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.main import app
from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJob,
    SlopeAnalysisJobStatus,
)
from src.modules.pivot_geometry_analysis.infrastructure.factories import (
    get_compute_slope_analysis,
    get_get_slope_analysis_job,
    get_get_slope_analysis_results,
    get_queue_slope_analysis,
)

_API_V1_PREFIX = "/api/v1"


def test_queue_slope_analysis_returns_accepted(client) -> None:
    """Test queuing a slope analysis job."""
    request_id = uuid4()

    class _QueueSlopeAnalysis:
        def execute(self, zone_id, profile_analysis_id, payload):
            return request_id

    app.dependency_overrides[get_queue_slope_analysis] = lambda: _QueueSlopeAnalysis()

    zone_id = uuid4()
    profile_analysis_id = uuid4()

    response = client.post(
        f"{_API_V1_PREFIX}/processes/slope-analysis/execution",
        json={
            "inputs": {
                "zone_id": str(zone_id),
                "profile_analysis_id": str(profile_analysis_id),
                "longitudinal_slope_config": {"limit_pct": 5.0, "limit_deg": 3.0},
                "transversal_slope_config": {"limit_pct": 3.0, "limit_deg": 2.0},
                "torsional_config": {"limit_pct": 2.0, "limit_deg": 1.0},
                "torsional_longitudinal_config": {"limit_pct": 4.0, "limit_deg": 2.5},
                "structural_stress_config": {"limit_pct": 10.0, "limit_deg": 6.0},
                "crop_clearance_h_boom_meters": 5.0,
                "crop_clearance_crop_risk_meters": 0.5,
                "crop_clearance_ground_risk_meters": 0.1,
            }
        },
    )

    assert response.status_code == 202, (
        f"Expected 202, got {response.status_code}: {response.json()}"
    )
    assert response.json()["request_id"] == str(request_id)
    assert response.json()["status"] == "queued"


def test_get_slope_analysis_job_returns_job_status(client) -> None:
    """Test retrieving slope analysis job status."""
    request_id = uuid4()
    zone_id = uuid4()
    profile_analysis_id = uuid4()

    class _GetSlopeAnalysisJob:
        def execute(self, req_id):
            assert req_id == request_id
            return SlopeAnalysisJob(
                request_id=request_id,
                zone_id=zone_id,
                profile_analysis_id=profile_analysis_id,
                status=SlopeAnalysisJobStatus.COMPLETED,
                payload={"test": "data"},
                result_payload={
                    "request_id": str(request_id),
                    "zone_id": str(zone_id),
                    "profile_analysis_id": str(profile_analysis_id),
                    "longitudinal_spans": 12,
                    "transversal_points": 120,
                    "torsional_spans": 12,
                    "structural_nodes": 11,
                    "structural_runs": 3,
                    "crop_clearance_points": 250,
                    "analytics_available": True,
                },
                error_message=None,
                queued_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )

    app.dependency_overrides[get_get_slope_analysis_job] = lambda: _GetSlopeAnalysisJob()

    response = client.get(f"{_API_V1_PREFIX}/processes/slope-analysis/jobs/{request_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["zone_id"] == str(zone_id)
    assert data["result_payload"] is not None
    assert data["result_payload"]["analytics_available"] is True
    assert "longitudinal_slope_analysis" not in data["result_payload"]


def test_get_slope_analysis_job_not_found(client) -> None:
    """Test retrieving non-existent slope analysis job."""

    class _GetSlopeAnalysisJob:
        def execute(self, req_id):
            return None

    app.dependency_overrides[get_get_slope_analysis_job] = lambda: _GetSlopeAnalysisJob()

    response = client.get(f"{_API_V1_PREFIX}/processes/slope-analysis/jobs/{uuid4()}")

    assert response.status_code == 404


def test_get_slope_analysis_job_normalizes_legacy_detailed_payload(client) -> None:
    """Legacy jobs with detailed payload are normalized to summary in /jobs/{id}."""
    request_id = uuid4()
    zone_id = uuid4()
    profile_analysis_id = uuid4()

    class _GetSlopeAnalysisJob:
        def execute(self, req_id):
            assert req_id == request_id
            return SlopeAnalysisJob(
                request_id=request_id,
                zone_id=zone_id,
                profile_analysis_id=profile_analysis_id,
                status=SlopeAnalysisJobStatus.COMPLETED,
                payload={"test": "data"},
                result_payload={
                    "request_id": str(request_id),
                    "longitudinal_slope_analysis": {
                        "request_id": str(request_id),
                        "spans": [{}, {}, {}],
                    },
                    "transversal_slope_analysis": {
                        "request_id": str(request_id),
                        "points": [{}, {}],
                    },
                    "torsional_slope_analysis": {
                        "request_id": str(request_id),
                        "spans": [{}],
                    },
                    "structural_stress_analysis": {
                        "request_id": str(request_id),
                        "nodes": [{}, {}],
                        "runs": [{}],
                    },
                    "crop_clearance_analysis": {
                        "request_id": str(request_id),
                        "points": [{}, {}, {}, {}],
                    },
                },
                error_message=None,
                queued_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )

    app.dependency_overrides[get_get_slope_analysis_job] = lambda: _GetSlopeAnalysisJob()

    response = client.get(f"{_API_V1_PREFIX}/processes/slope-analysis/jobs/{request_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["result_payload"]["longitudinal_spans"] == 3
    assert data["result_payload"]["transversal_points"] == 2
    assert data["result_payload"]["torsional_spans"] == 1
    assert data["result_payload"]["structural_nodes"] == 2
    assert data["result_payload"]["structural_runs"] == 1
    assert data["result_payload"]["crop_clearance_points"] == 4
    assert data["result_payload"]["analytics_available"] is True
    assert "longitudinal_slope_analysis" not in data["result_payload"]


def test_get_slope_analysis_results_returns_results(client) -> None:
    """Test retrieving slope analysis results."""
    request_id = uuid4()

    result_payload = {
        "longitudinal_slope_analysis": {"spans": []},
        "transversal_slope_analysis": {"points": []},
        "torsional_slope_analysis": {"spans": []},
        "structural_stress_analysis": {"nodes": [], "runs": []},
        "crop_clearance_analysis": {"points": []},
    }

    class _GetSlopeAnalysisResults:
        def execute(self, req_id):
            assert req_id == request_id
            return result_payload

    app.dependency_overrides[get_get_slope_analysis_results] = lambda: _GetSlopeAnalysisResults()

    response = client.get(f"{_API_V1_PREFIX}/processes/slope-analysis/jobs/{request_id}/results")

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == str(request_id)
    assert "longitudinal_slope_analysis" in data["result_payload"]


@pytest.mark.parametrize(
    "path_suffix,section_key",
    [
        ("longitudinal-slope", "longitudinal_slope_analysis"),
        ("transversal-slope", "transversal_slope_analysis"),
        ("torsional-slope", "torsional_slope_analysis"),
        ("structural-stress", "structural_stress_analysis"),
        ("crop-clearance", "crop_clearance_analysis"),
    ],
)
def test_get_specific_slope_analysis_results_returns_only_section(
    client, path_suffix: str, section_key: str
) -> None:
    request_id = uuid4()

    result_payload = {
        "longitudinal_slope_analysis": {"spans": [1]},
        "transversal_slope_analysis": {"points": [2]},
        "torsional_slope_analysis": {"spans": [3]},
        "structural_stress_analysis": {"nodes": [4], "runs": [5]},
        "crop_clearance_analysis": {"points": [6]},
    }

    class _GetSlopeAnalysisResults:
        def execute(self, req_id):
            assert req_id == request_id
            return result_payload

    app.dependency_overrides[get_get_slope_analysis_results] = lambda: _GetSlopeAnalysisResults()

    response = client.get(
        f"{_API_V1_PREFIX}/processes/slope-analysis/jobs/{request_id}/results/{path_suffix}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == str(request_id)
    assert data["result_payload"] == result_payload[section_key]


@pytest.mark.parametrize(
    "path_suffix",
    [
        "longitudinal-slope",
        "transversal-slope",
        "torsional-slope",
        "structural-stress",
        "crop-clearance",
    ],
)
def test_get_specific_slope_analysis_results_not_found(client, path_suffix: str) -> None:
    """Test specific result endpoint when job is missing/incomplete."""

    class _GetSlopeAnalysisResults:
        def execute(self, req_id):
            return None

    app.dependency_overrides[get_get_slope_analysis_results] = lambda: _GetSlopeAnalysisResults()

    response = client.get(
        f"{_API_V1_PREFIX}/processes/slope-analysis/jobs/{uuid4()}/results/{path_suffix}"
    )

    assert response.status_code == 404


def test_get_slope_analysis_results_not_found(client) -> None:
    """Test retrieving results for non-existent job or incomplete job."""

    class _GetSlopeAnalysisResults:
        def execute(self, req_id):
            return None

    app.dependency_overrides[get_get_slope_analysis_results] = lambda: _GetSlopeAnalysisResults()

    response = client.get(f"{_API_V1_PREFIX}/processes/slope-analysis/jobs/{uuid4()}/results")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Compute (ephemeral) endpoints
# ---------------------------------------------------------------------------

_COMPUTE_RESULT_PAYLOAD = {
    "request_id": "00000000-0000-0000-0000-000000000001",
    "longitudinal_slope_analysis": {"request_id": "...", "spans": [{"azimuth_deg": 0.0}]},
    "transversal_slope_analysis": {"request_id": "...", "points": [{"radius_m": 50.0}]},
    "torsional_slope_analysis": {"request_id": "...", "spans": [{"azimuth_deg": 0.0}]},
    "structural_stress_analysis": {
        "request_id": "...",
        "nodes": [{"tower_index": 0}],
        "runs": [{"run_kind": "tension"}],
    },
    "crop_clearance_analysis": {"request_id": "...", "points": [{"azimuth_deg": 0.0}]},
}

_COMPUTE_REQUEST_BODY = {
    "inputs": {
        "profile_analysis_id": str(uuid4()),
    }
}


def _make_compute_use_case():
    class _ComputeSlopeAnalysis:
        def execute(self, profile_analysis_id, payload):
            return _COMPUTE_RESULT_PAYLOAD

    return _ComputeSlopeAnalysis()


def test_compute_slope_analysis_returns_all_sections(client) -> None:
    """POST /compute returns all analysis sections in result_payload."""
    app.dependency_overrides[get_compute_slope_analysis] = lambda: _make_compute_use_case()

    response = client.post(
        f"{_API_V1_PREFIX}/processes/slope-analysis/compute",
        json=_COMPUTE_REQUEST_BODY,
    )

    assert response.status_code == 200
    data = response.json()
    assert "longitudinal_slope_analysis" in data["result_payload"]
    assert "transversal_slope_analysis" in data["result_payload"]
    assert "torsional_slope_analysis" in data["result_payload"]
    assert "structural_stress_analysis" in data["result_payload"]
    assert "crop_clearance_analysis" in data["result_payload"]


@pytest.mark.parametrize(
    "path_suffix,section_key",
    [
        ("longitudinal-slope", "longitudinal_slope_analysis"),
        ("transversal-slope", "transversal_slope_analysis"),
        ("torsional-slope", "torsional_slope_analysis"),
        ("structural-stress", "structural_stress_analysis"),
        ("crop-clearance", "crop_clearance_analysis"),
    ],
)
def test_compute_specific_slope_analysis_returns_only_section(
    client, path_suffix: str, section_key: str
) -> None:
    """POST /compute/{analysis} returns only the requested section."""
    app.dependency_overrides[get_compute_slope_analysis] = lambda: _make_compute_use_case()

    response = client.post(
        f"{_API_V1_PREFIX}/processes/slope-analysis/compute/{path_suffix}",
        json=_COMPUTE_REQUEST_BODY,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["result_payload"] == _COMPUTE_RESULT_PAYLOAD[section_key]
    # Other sections must NOT appear at the top level of result_payload
    for other_key in _COMPUTE_RESULT_PAYLOAD:
        if other_key not in ("request_id", section_key):
            assert other_key not in data["result_payload"]


def test_compute_slope_analysis_propagates_error_as_422(client) -> None:
    """Computation errors surface as 422 Unprocessable Entity."""

    class _FailingComputeUseCase:
        def execute(self, profile_analysis_id, payload):
            raise ValueError("profiles not found for the given id")

    app.dependency_overrides[get_compute_slope_analysis] = lambda: _FailingComputeUseCase()

    response = client.post(
        f"{_API_V1_PREFIX}/processes/slope-analysis/compute",
        json=_COMPUTE_REQUEST_BODY,
    )

    assert response.status_code == 422
