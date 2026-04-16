from datetime import datetime, timezone
from uuid import uuid4

import src.modules.profile_analysis.presentation.processes_router as profile_router
from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisAnalytics,
    ProfileAnalysisJob,
    ProfileAnalysisJobStatus,
)


def test_queue_profile_analysis_returns_accepted(client, monkeypatch) -> None:
    request_id = uuid4()

    class _QueueProfileAnalysis:
        def execute(self, zone_id, payload):
            return request_id

    monkeypatch.setattr(profile_router, "get_queue_profile_analysis", lambda db: _QueueProfileAnalysis())

    response = client.post(
        "/processes/profile-analysis/execution",
        json={
            "inputs": {
                "zone_id": str(uuid4()),
                "pivot_kind": "circular",
                "center": [-74.05, 4.61],
                "radii_m": [100.0, 200.0],
                "transverse_spacing_m": 10.0,
                "longitudinal_spacing_m": 10.0,
                "angular_spacing_deg": 45.0,
            }
        },
    )

    assert response.status_code == 202
    assert response.json()["request_id"] == str(request_id)
    assert response.json()["status"] == "queued"


def test_get_profile_analysis_job_returns_persisted_status(client, monkeypatch) -> None:
    request_id = uuid4()
    zone_id = uuid4()

    class _GetProfileAnalysisJob:
        def execute(self, requested_id):
            assert requested_id == request_id
            return ProfileAnalysisJob(
                request_id=request_id,
                zone_id=zone_id,
                status=ProfileAnalysisJobStatus.COMPLETED,
                payload={"inputs": {}},
                result_payload={"total_points": 42},
                error_message=None,
                queued_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )

    monkeypatch.setattr(profile_router, "get_get_profile_analysis_job", lambda db: _GetProfileAnalysisJob())

    response = client.get(f"/processes/profile-analysis/jobs/{request_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["result_payload"] == {"total_points": 42}


def test_get_profile_analysis_analytics_returns_aggregated_result(client, monkeypatch) -> None:
    request_id = uuid4()

    class _GetProfileAnalysisAnalytics:
        def execute(self, requested_id):
            assert requested_id == request_id
            return ProfileAnalysisAnalytics(
                request_id=request_id,
                total_points=120,
                min_elevation_m=100.0,
                max_elevation_m=135.0,
                avg_elevation_m=118.5,
            )

    monkeypatch.setattr(
        profile_router,
        "get_get_profile_analysis_analytics",
        lambda: _GetProfileAnalysisAnalytics(),
    )

    response = client.get(f"/processes/profile-analysis/jobs/{request_id}/analytics")

    assert response.status_code == 200
    assert response.json()["total_points"] == 120
    assert response.json()["avg_elevation_m"] == 118.5
