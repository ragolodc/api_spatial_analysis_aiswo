from datetime import datetime, timezone
from uuid import UUID

from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisJob,
    ProfileAnalysisJobStatus,
)
from src.modules.profile_analysis.domain.ports import ProfileAnalysisJobRepository


class PersistProfileAnalysisJob:
    """Application command to persist profile-analysis job lifecycle transitions."""

    def __init__(self, repository: ProfileAnalysisJobRepository) -> None:
        self._repository = repository

    def queue(self, request_id: UUID, zone_id: UUID, payload: dict) -> ProfileAnalysisJob:
        job = ProfileAnalysisJob(
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
        return self._repository.save(job)

    def mark_running(self, request_id: UUID) -> ProfileAnalysisJob:
        job = self._require_job(request_id)
        return self._repository.update(
            ProfileAnalysisJob(
                request_id=job.request_id,
                zone_id=job.zone_id,
                status=ProfileAnalysisJobStatus.RUNNING,
                payload=job.payload,
                result_payload=job.result_payload,
                error_message=None,
                queued_at=job.queued_at,
                started_at=datetime.now(timezone.utc),
                completed_at=None,
            )
        )

    def mark_completed(self, request_id: UUID, result_payload: dict) -> ProfileAnalysisJob:
        job = self._require_job(request_id)
        return self._repository.update(
            ProfileAnalysisJob(
                request_id=job.request_id,
                zone_id=job.zone_id,
                status=ProfileAnalysisJobStatus.COMPLETED,
                payload=job.payload,
                result_payload=result_payload,
                error_message=None,
                queued_at=job.queued_at,
                started_at=job.started_at,
                completed_at=datetime.now(timezone.utc),
            )
        )

    def mark_failed(self, request_id: UUID, error_message: str) -> ProfileAnalysisJob:
        job = self._require_job(request_id)
        return self._repository.update(
            ProfileAnalysisJob(
                request_id=job.request_id,
                zone_id=job.zone_id,
                status=ProfileAnalysisJobStatus.FAILED,
                payload=job.payload,
                result_payload=None,
                error_message=error_message,
                queued_at=job.queued_at,
                started_at=job.started_at,
                completed_at=datetime.now(timezone.utc),
            )
        )

    def _require_job(self, request_id: UUID) -> ProfileAnalysisJob:
        job = self._repository.find_by_id(request_id)
        if job is None:
            raise ValueError(f"ProfileAnalysisJob {request_id} not found")
        return job
