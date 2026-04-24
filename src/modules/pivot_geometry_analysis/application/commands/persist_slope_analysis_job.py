from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJob,
    SlopeAnalysisJobStatus,
)
from src.modules.pivot_geometry_analysis.domain.exceptions import SlopeAnalysisJobNotFound
from src.modules.pivot_geometry_analysis.domain.ports import SlopeAnalysisJobRepository


class PersistSlopeAnalysisJob:
    def __init__(self, repository: SlopeAnalysisJobRepository) -> None:
        self._repository = repository

    def queue(self, request_id: UUID, zone_id: UUID, payload: dict[str, Any]) -> SlopeAnalysisJob:
        job = SlopeAnalysisJob(
            request_id=request_id,
            zone_id=zone_id,
            status=SlopeAnalysisJobStatus.QUEUED,
            payload=payload,
            result_payload=None,
            error_message=None,
            queued_at=datetime.now(timezone.utc),
        )
        return self._repository.save(job)

    def mark_running(self, request_id: UUID) -> SlopeAnalysisJob:
        return self._transition(
            request_id=request_id, status=SlopeAnalysisJobStatus.RUNNING, set_started_at=True
        )

    def mark_completed(self, request_id: UUID, result_payload: dict[str, Any]) -> SlopeAnalysisJob:
        return self._transition(
            request_id=request_id,
            status=SlopeAnalysisJobStatus.COMPLETED,
            result_payload=result_payload,
            set_completed_at=True,
        )

    def mark_failed(self, request_id: UUID, error_message: str) -> SlopeAnalysisJob:
        return self._transition(
            request_id=request_id,
            status=SlopeAnalysisJobStatus.FAILED,
            error_message=error_message,
            set_completed_at=True,
        )

    def _transition(
        self,
        request_id: UUID,
        status: SlopeAnalysisJobStatus,
        *,
        result_payload: dict[str, Any] | None = None,
        error_message: str | None = None,
        set_started_at: bool = False,
        set_completed_at: bool = False,
    ) -> SlopeAnalysisJob:
        job = self._require_job(request_id=request_id)
        now = datetime.now(timezone.utc)
        return self._repository.update(
            SlopeAnalysisJob(
                request_id=job.request_id,
                zone_id=job.zone_id,
                status=status,
                payload=job.payload,
                result_payload=result_payload if result_payload is not None else job.result_payload,
                error_message=error_message,
                queued_at=job.queued_at,
                started_at=now if set_started_at else job.started_at,
                completed_at=now if set_completed_at else job.completed_at,
            )
        )

    def _require_job(self, request_id: UUID) -> SlopeAnalysisJob:
        job = self._repository.find_by_id(request_id=request_id)
        if job is None:
            raise SlopeAnalysisJobNotFound(f"SlopeAnalysisJob {request_id} not found")
        return job
