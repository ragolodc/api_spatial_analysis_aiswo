from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisJob,
    ProfileAnalysisJobStatus,
)
from src.modules.profile_analysis.domain.ports import ProfileAnalysisJobRepository
from src.modules.profile_analysis.infrastructure.persistence.models import (
    ProfileAnalysisJobModel,
)


class SQLAlchemyProfileAnalysisJobRepository(ProfileAnalysisJobRepository):
    """SQLAlchemy persistence for profile analysis jobs."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def save(self, job: ProfileAnalysisJob) -> ProfileAnalysisJob:
        model = ProfileAnalysisJobModel(
            request_id=job.request_id,
            zone_id=job.zone_id,
            status=job.status.value,
            payload=job.payload,
            result_payload=job.result_payload,
            error_message=job.error_message,
            queued_at=job.queued_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, request_id: UUID) -> ProfileAnalysisJob | None:
        model = self._db.get(ProfileAnalysisJobModel, request_id)
        return self._to_entity(model) if model else None

    def update(self, job: ProfileAnalysisJob) -> ProfileAnalysisJob:
        model = self._db.get(ProfileAnalysisJobModel, job.request_id)
        if model is None:
            raise ValueError(f"ProfileAnalysisJob {job.request_id} not found")

        model.status = job.status.value
        model.payload = job.payload
        model.result_payload = job.result_payload
        model.error_message = job.error_message
        model.queued_at = job.queued_at
        model.started_at = job.started_at
        model.completed_at = job.completed_at
        self._db.commit()
        self._db.refresh(model)
        return self._to_entity(model)

    def _to_entity(self, model: ProfileAnalysisJobModel) -> ProfileAnalysisJob:
        return ProfileAnalysisJob(
            request_id=model.request_id,
            zone_id=model.zone_id,
            status=ProfileAnalysisJobStatus(model.status),
            payload=model.payload,
            result_payload=model.result_payload,
            error_message=model.error_message,
            queued_at=model.queued_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )
