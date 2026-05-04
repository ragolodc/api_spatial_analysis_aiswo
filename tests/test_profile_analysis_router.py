from datetime import datetime, timezone
from uuid import uuid4

from src.main import app
from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisAnalytics,
    ProfileAnalysisJob,
    ProfileAnalysisJobStatus,
    ProfilePointFilters,
    ProfilePointRow,
    ProfileSummaryEntry,
    ProfileType,
)
from src.modules.profile_analysis.infrastructure.factories import (
    get_get_profile_analysis_analytics,
    get_get_profile_analysis_job,
    get_get_profile_analysis_summary,
    get_queue_profile_analysis,
)
from src.modules.profile_analysis.presentation.processes_router import (
    _resolve_get_profile_analysis_points_use_case,
)

_API_V1_PREFIX = "/api/v1"


def test_queue_profile_analysis_returns_accepted(client) -> None:
    request_id = uuid4()

    class _QueueProfileAnalysis:
        def execute(self, zone_id, payload):
            return request_id

    app.dependency_overrides[get_queue_profile_analysis] = lambda: _QueueProfileAnalysis()

    response = client.post(
        f"{_API_V1_PREFIX}/processes/profile-analysis/execution",
        json={
            "inputs": {
                "zone_id": str(uuid4()),
                "pivot_kind": "circular",
                "center": [-74.05, 4.61],
                "radii_m": [100.0, 200.0],
                "spans": [
                    {"position": 1, "length": 100, "dry_weight": 29, "service_weight": 45},
                    {"position": 2, "length": 200, "dry_weight": 30, "service_weight": 40},
                ],
                "transverse_spacing_m": 10.0,
                "longitudinal_spacing_m": 10.0,
                "angular_spacing_deg": 45.0,
            }
        },
    )

    assert response.status_code == 202
    assert response.json()["request_id"] == str(request_id)
    assert response.json()["status"] == "queued"


def test_get_profile_analysis_job_returns_persisted_status(client) -> None:
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

    app.dependency_overrides[get_get_profile_analysis_job] = lambda: _GetProfileAnalysisJob()

    response = client.get(f"{_API_V1_PREFIX}/processes/profile-analysis/jobs/{request_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["result_payload"] == {"total_points": 42}


def test_get_profile_analysis_analytics_returns_aggregated_result(client) -> None:
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

    app.dependency_overrides[get_get_profile_analysis_analytics] = lambda: (
        _GetProfileAnalysisAnalytics()
    )

    response = client.get(
        f"{_API_V1_PREFIX}/processes/profile-analysis/jobs/{request_id}/analytics"
    )

    assert response.status_code == 200
    assert response.json()["total_points"] == 120
    assert response.json()["avg_elevation_m"] == 118.5


def test_get_profile_analysis_points_returns_paginated_rows(client) -> None:
    request_id = uuid4()

    class _GetProfileAnalysisPoints:
        def execute(self, request_id, profile_type, filters, limit, offset):
            assert request_id is not None
            assert profile_type is None
            assert filters == ProfilePointFilters()
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

    app.dependency_overrides[_resolve_get_profile_analysis_points_use_case] = lambda: (
        lambda: _GetProfileAnalysisPoints()
    )

    response = client.get(
        f"{_API_V1_PREFIX}/processes/profile-analysis/jobs/{request_id}/points?limit=10&offset=0"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["items"][0]["profile_type"] == "transverse"
    assert data["items"][0]["elevation_m"] == 120.5


def test_get_profile_analysis_points_applies_explicit_filters(client) -> None:
    request_id = uuid4()

    class _GetProfileAnalysisPoints:
        def execute(self, request_id, profile_type, filters, limit, offset):
            assert request_id is not None
            assert profile_type == ProfileType.TRANSVERSE
            assert filters == ProfilePointFilters(
                profile_key="radius:100.0",
                min_distance_m=50.0,
                max_distance_m=150.0,
                min_elevation_m=110.0,
                max_elevation_m=130.0,
            )
            assert limit == 25
            assert offset == 5
            return []

    app.dependency_overrides[_resolve_get_profile_analysis_points_use_case] = lambda: (
        lambda: _GetProfileAnalysisPoints()
    )

    response = client.get(
        f"{_API_V1_PREFIX}/processes/profile-analysis/jobs/{request_id}/points"
        "?profile_type=transverse"
        "&profile_key=radius:100.0"
        "&min_distance_m=50"
        "&max_distance_m=150"
        "&min_elevation_m=110"
        "&max_elevation_m=130"
        "&limit=25"
        "&offset=5"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["limit"] == 25
    assert data["offset"] == 5


def test_get_profile_analysis_points_rejects_invalid_profile_type(client) -> None:
    class _Stub:
        def execute(self, *args, **kwargs):
            raise AssertionError("Should not be called")

    app.dependency_overrides[_resolve_get_profile_analysis_points_use_case] = lambda: (
        lambda: _Stub()
    )

    request_id = uuid4()
    response = client.get(
        f"{_API_V1_PREFIX}/processes/profile-analysis/jobs/{request_id}/points?profile_type=invalid"
    )
    assert response.status_code == 422


def test_get_profile_analysis_points_rejects_invalid_filter_range(client) -> None:
    class _Stub:
        def execute(self, *args, **kwargs):
            raise AssertionError("Should not be called")

    app.dependency_overrides[_resolve_get_profile_analysis_points_use_case] = lambda: (
        lambda: _Stub()
    )

    request_id = uuid4()
    response = client.get(
        f"{_API_V1_PREFIX}/processes/profile-analysis/jobs/{request_id}/points"
        "?min_distance_m=200&max_distance_m=100"
    )

    assert response.status_code == 422


def test_get_profile_analysis_points_invalid_filters_do_not_resolve_use_case(
    client, monkeypatch
) -> None:
    use_case_resolved = False

    def _raise_if_resolved():
        nonlocal use_case_resolved
        use_case_resolved = True
        raise AssertionError("Use case factory should not be resolved")

    monkeypatch.setattr(
        "src.modules.profile_analysis.presentation.processes_router.get_get_profile_analysis_points",
        _raise_if_resolved,
    )

    request_id = uuid4()
    response = client.get(
        f"{_API_V1_PREFIX}/processes/profile-analysis/jobs/{request_id}/points"
        "?min_distance_m=200&max_distance_m=100"
    )

    assert response.status_code == 422
    assert use_case_resolved is False


def test_get_profile_analysis_summary_returns_per_profile_stats(client) -> None:
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

    app.dependency_overrides[get_get_profile_analysis_summary] = lambda: (
        _GetProfileAnalysisSummary()
    )

    response = client.get(f"{_API_V1_PREFIX}/processes/profile-analysis/jobs/{request_id}/summary")

    assert response.status_code == 200
    data = response.json()
    assert len(data["profiles"]) == 2
    assert data["profiles"][0]["profile_key"] == "radius:100.0"
    assert data["profiles"][1]["profile_type"] == "longitudinal"
