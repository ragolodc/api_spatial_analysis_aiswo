from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.pivot_geometry_analysis.domain.entities import SlopeAnalysisJobStatus
from src.modules.pivot_geometry_analysis.domain.exceptions import SlopeAnalysisJobNotFound
from src.modules.pivot_geometry_analysis.domain.ports import (
    SlopeAnalysisJob,
    SlopeAnalysisJobRepository,
)
from src.modules.pivot_geometry_analysis.infrastructure.persistence.models import (
    SlopeAnalysisJobModel,
)


class SQLAlchemySlopeAnalysisJobRepository(SlopeAnalysisJobRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def save(self, job: SlopeAnalysisJob) -> SlopeAnalysisJob:
        model = SlopeAnalysisJobModel(
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

    def find_by_id(self, request_id: UUID) -> SlopeAnalysisJob | None:
        model = self._db.get(SlopeAnalysisJobModel, request_id)
        return self._to_entity(model) if model else None

    def update(self, job: SlopeAnalysisJob) -> SlopeAnalysisJob | None:
        model = self._db.get(SlopeAnalysisJobModel, job.request_id)
        if model is None:
            raise SlopeAnalysisJobNotFound(
                f"SlopeAnalysisJob {job.request_id!s} not found — cannot update a non-existent job"
            )
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

    def _to_entity(self, model: SlopeAnalysisJobModel) -> SlopeAnalysisJob:
        return SlopeAnalysisJob(
            request_id=model.request_id,
            zone_id=model.zone_id,
            status=SlopeAnalysisJobStatus(model.status),
            payload=model.payload,
            result_payload=model.result_payload,
            error_message=model.error_message,
            queued_at=model.queued_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )
