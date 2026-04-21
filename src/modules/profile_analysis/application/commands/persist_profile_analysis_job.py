from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisJob,
    ProfileAnalysisJobStatus,
)
from src.modules.profile_analysis.domain.exceptions import ProfileAnalysisJobNotFound
from src.modules.profile_analysis.domain.ports import ProfileAnalysisJobRepository

_MAX_ERROR_MESSAGE_LEN = 1000


class PersistProfileAnalysisJob:
    """Application command to persist profile-analysis job lifecycle transitions."""

    def __init__(self, repository: ProfileAnalysisJobRepository) -> None:
        self._repository = repository

    def queue(self, request_id: UUID, zone_id: UUID, payload: dict[str, Any]) -> ProfileAnalysisJob:
        job = ProfileAnalysisJob(
            request_id=request_id,
            zone_id=zone_id,
            status=ProfileAnalysisJobStatus.QUEUED,
            payload=payload,
            result_payload=None,
            error_message=None,
            queued_at=datetime.now(timezone.utc),
        )
        return self._repository.save(job)

    def mark_running(self, request_id: UUID) -> ProfileAnalysisJob:
        return self._transition(
            request_id,
            ProfileAnalysisJobStatus.RUNNING,
            set_started_at=True,
        )

    def mark_completed(
        self, request_id: UUID, result_payload: dict[str, Any]
    ) -> ProfileAnalysisJob:
        return self._transition(
            request_id,
            ProfileAnalysisJobStatus.COMPLETED,
            result_payload=result_payload,
            set_completed_at=True,
        )

    def mark_failed(self, request_id: UUID, error_message: str) -> ProfileAnalysisJob:
        return self._transition(
            request_id,
            ProfileAnalysisJobStatus.FAILED,
            error_message=error_message[:_MAX_ERROR_MESSAGE_LEN],
            set_completed_at=True,
        )

    def _transition(
        self,
        request_id: UUID,
        status: ProfileAnalysisJobStatus,
        *,
        result_payload: dict[str, Any] | None = None,
        error_message: str | None = None,
        set_started_at: bool = False,
        set_completed_at: bool = False,
    ) -> ProfileAnalysisJob:
        job = self._require_job(request_id)
        now = datetime.now(timezone.utc)
        return self._repository.update(
            ProfileAnalysisJob(
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

    def _require_job(self, request_id: UUID) -> ProfileAnalysisJob:
        job = self._repository.find_by_id(request_id)
        if job is None:
            raise ProfileAnalysisJobNotFound(f"ProfileAnalysisJob {request_id} not found")
        return job
