from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisJob,
    ProfileAnalysisJobRequest,
    ProfileAnalysisJobStatus,
)
from src.modules.profile_analysis.domain.ports import (
    ProfileAnalysisJobDispatcher,
    ProfileAnalysisJobRepository,
)


class QueueProfileAnalysis:
    """Application command that enqueues a profile-analysis job."""

    def __init__(
        self,
        dispatcher: ProfileAnalysisJobDispatcher,
        job_repository: ProfileAnalysisJobRepository,
    ) -> None:
        self._dispatcher = dispatcher
        self._job_repository = job_repository

    def execute(self, zone_id: UUID, payload: dict) -> UUID:
        request_id = uuid4()
        self._job_repository.save(
            ProfileAnalysisJob(
                request_id=request_id,
                zone_id=zone_id,
                status=ProfileAnalysisJobStatus.QUEUED,
                payload=payload,
                result_payload=None,
                error_message=None,
                queued_at=datetime.now(timezone.utc),
                started_at=None,
                completed_at=None,
            )
        )
        request = ProfileAnalysisJobRequest(
            request_id=request_id,
            zone_id=zone_id,
            payload=payload,
        )
        self._dispatcher.dispatch(request)
        return request_id
