from datetime import datetime, timezone
from uuid import uuid4

from src.modules.profile_analysis.application import GetProfileAnalysisJob, GetProfileAnalysisPoints
from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisJob,
    ProfileAnalysisJobStatus,
    ProfilePointFilters,
    ProfileType,
)


class FakeJobRepository:
    def __init__(self, job) -> None:
        self.job = job

    def find_by_id(self, request_id):
        return self.job if self.job.request_id == request_id else None


class FakePointWarehouse:
    def __init__(self) -> None:
        self.calls = []

    def get_points(self, request_id, profile_type, filters, limit, offset):
        self.calls.append(
            {
                "request_id": request_id,
                "profile_type": profile_type,
                "filters": filters,
                "limit": limit,
                "offset": offset,
            }
        )
        return []


def test_get_profile_analysis_job_returns_job_from_repository() -> None:
    job = ProfileAnalysisJob(
        request_id=uuid4(),
        zone_id=uuid4(),
        status=ProfileAnalysisJobStatus.QUEUED,
        payload={"inputs": {}},
        result_payload=None,
        error_message=None,
        queued_at=datetime.now(timezone.utc),
        started_at=None,
        completed_at=None,
    )

    result = GetProfileAnalysisJob(FakeJobRepository(job)).execute(job.request_id)

    assert result is not None
    assert result.request_id == job.request_id


def test_get_profile_analysis_points_passes_filters_to_warehouse() -> None:
    warehouse = FakePointWarehouse()
    request_id = uuid4()
    filters = ProfilePointFilters(profile_key="radius:100.0", min_distance_m=25.0)

    result = GetProfileAnalysisPoints(warehouse).execute(
        request_id=request_id,
        profile_type=ProfileType.TRANSVERSE,
        filters=filters,
        limit=50,
        offset=10,
    )

    assert result == []
    assert warehouse.calls == [
        {
            "request_id": request_id,
            "profile_type": ProfileType.TRANSVERSE,
            "filters": filters,
            "limit": 50,
            "offset": 10,
        }
    ]
