from typing import Any
from uuid import UUID, uuid4

from src.modules.pivot_geometry_analysis.application.commands import (
    PersistSlopeAnalysisJob,
)
from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJobRequest,
)
from src.modules.pivot_geometry_analysis.domain.ports import SlopeAnalysisJobDispatcher


class QueueSlopeAnalysis:
    """Application command that persists and enqueues a slope-analysis job."""

    def __init__(
        self,
        dispatcher: SlopeAnalysisJobDispatcher,
        persist_job: PersistSlopeAnalysisJob,
    ) -> None:
        self._dispatcher = dispatcher
        self._persist_job = persist_job

    def execute(self, zone_id: UUID, payload: dict[str, Any]) -> UUID:
        request_id = uuid4()
        self._persist_job.queue(request_id=request_id, zone_id=zone_id, payload=payload)
        self._dispatcher.dispatch(
            SlopeAnalysisJobRequest(request_id=request_id, zone_id=zone_id, payload=payload)
        )
        return request_id
