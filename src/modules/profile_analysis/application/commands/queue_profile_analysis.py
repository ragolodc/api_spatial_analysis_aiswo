from typing import Any
from uuid import UUID, uuid4

from src.modules.profile_analysis.domain.entities import ProfileAnalysisJobRequest
from src.modules.profile_analysis.domain.ports import ProfileAnalysisJobDispatcher
from src.modules.profile_analysis.application.commands.persist_profile_analysis_job import (
    PersistProfileAnalysisJob,
)


class QueueProfileAnalysis:
    """Application command that persists and enqueues a profile-analysis job."""

    def __init__(
        self,
        dispatcher: ProfileAnalysisJobDispatcher,
        persist_job: PersistProfileAnalysisJob,
    ) -> None:
        self._dispatcher = dispatcher
        self._persist_job = persist_job

    def execute(self, zone_id: UUID, payload: dict[str, Any]) -> UUID:
        request_id = uuid4()
        self._persist_job.queue(request_id, zone_id, payload)
        self._dispatcher.dispatch(
            ProfileAnalysisJobRequest(
                request_id=request_id,
                zone_id=zone_id,
                payload=payload,
            )
        )
        return request_id

        request = ProfileAnalysisJobRequest(
            request_id=request_id,
            zone_id=zone_id,
            payload=payload,
        )
        self._dispatcher.dispatch(request)
        return request_id
