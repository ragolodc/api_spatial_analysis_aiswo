from datetime import datetime, timezone
from uuid import uuid4

from src.modules.profile_analysis.application import GetProfileAnalysisJob
from src.modules.profile_analysis.domain.entities import ProfileAnalysisJob, ProfileAnalysisJobStatus


class FakeJobRepository:
    def __init__(self, job) -> None:
        self.job = job

    def find_by_id(self, request_id):
        return self.job if self.job.request_id == request_id else None


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
