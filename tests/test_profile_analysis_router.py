from datetime import datetime, timezone
from uuid import uuid4

import src.modules.profile_analysis.presentation.processes_router as profile_router
from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisAnalytics,
    ProfileAnalysisJob,
    ProfileAnalysisJobStatus,
    ProfilePointRow,
    ProfileSummaryEntry,
    ProfileType,
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


def test_get_profile_analysis_points_returns_paginated_rows(client, monkeypatch) -> None:
    request_id = uuid4()

    class _GetProfileAnalysisPoints:
        def execute(self, request_id, profile_type, limit, offset):
            return [
                ProfilePointRow(
                    profile_type=ProfileType.TRANSVERSE,
                    profile_key="radius:100.0",
                    point_index=0,
                    radius_m=100.0,
                    angle_deg=0.0,
                    distance_m=100.0,
                    longitude=-74.05,
                    latitude=4.61,
                    elevation_m=120.5,
                )
            ]

    monkeypatch.setattr(
        profile_router,
        "get_get_profile_analysis_points",
        lambda: _GetProfileAnalysisPoints(),
    )

    response = client.get(f"/processes/profile-analysis/jobs/{request_id}/points?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["items"][0]["profile_type"] == "transverse"
    assert data["items"][0]["elevation_m"] == 120.5


def test_get_profile_analysis_points_rejects_invalid_profile_type(client, monkeypatch) -> None:
    request_id = uuid4()
    response = client.get(f"/processes/profile-analysis/jobs/{request_id}/points?profile_type=invalid")
    assert response.status_code == 400


def test_get_profile_analysis_summary_returns_per_profile_stats(client, monkeypatch) -> None:
    request_id = uuid4()

    class _GetProfileAnalysisSummary:
        def execute(self, req_id):
            return [
                ProfileSummaryEntry(
                    profile_type=ProfileType.TRANSVERSE,
                    profile_key="radius:100.0",
                    total_points=36,
                    min_elevation_m=105.0,
                    max_elevation_m=135.0,
                    avg_elevation_m=118.5,
                ),
                ProfileSummaryEntry(
                    profile_type=ProfileType.LONGITUDINAL,
                    profile_key="azimuth:0.0",
                    total_points=10,
                    min_elevation_m=110.0,
                    max_elevation_m=130.0,
                    avg_elevation_m=120.0,
                ),
            ]

    monkeypatch.setattr(
        profile_router,
        "get_get_profile_analysis_summary",
        lambda: _GetProfileAnalysisSummary(),
    )

    response = client.get(f"/processes/profile-analysis/jobs/{request_id}/summary")

    assert response.status_code == 200
    data = response.json()
    assert len(data["profiles"]) == 2
    assert data["profiles"][0]["profile_key"] == "radius:100.0"
    assert data["profiles"][1]["profile_type"] == "longitudinal"
