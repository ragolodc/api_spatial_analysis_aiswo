"""Tests for slope analysis endpoints."""

from datetime import datetime, timezone
from uuid import uuid4

from src.main import app
from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJob,
    SlopeAnalysisJobStatus,
)
from src.modules.pivot_geometry_analysis.infrastructure.factories import (
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
                    "longitudinal_slope_analysis": {"spans": []},
                    "transversal_slope_analysis": {"points": []},
                    "torsional_slope_analysis": {"spans": []},
                    "structural_stress_analysis": {"nodes": [], "runs": []},
                    "crop_clearance_analysis": {"points": []},
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


def test_get_slope_analysis_job_not_found(client) -> None:
    """Test retrieving non-existent slope analysis job."""

    class _GetSlopeAnalysisJob:
        def execute(self, req_id):
            return None

    app.dependency_overrides[get_get_slope_analysis_job] = lambda: _GetSlopeAnalysisJob()

    response = client.get(f"{_API_V1_PREFIX}/processes/slope-analysis/jobs/{uuid4()}")

    assert response.status_code == 404


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


def test_get_slope_analysis_results_not_found(client) -> None:
    """Test retrieving results for non-existent job or incomplete job."""

    class _GetSlopeAnalysisResults:
        def execute(self, req_id):
            return None

    app.dependency_overrides[get_get_slope_analysis_results] = lambda: _GetSlopeAnalysisResults()

    response = client.get(f"{_API_V1_PREFIX}/processes/slope-analysis/jobs/{uuid4()}/results")

    assert response.status_code == 404
