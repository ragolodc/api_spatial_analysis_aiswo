"""Async tasks for profile analysis."""

import logging
from typing import Any
from uuid import UUID

import src.shared.db.registry  # noqa: F401 — ensures all ORM models are registered before SQLAlchemy resolves FKs
from src.modules.profile_analysis.application.commands import (
    PersistProfileAnalysisJob,
    PersistProfileAnalysisPoints,
)
from src.modules.profile_analysis.domain.entities import ProfileAnalysisJobRequest
from src.modules.profile_analysis.infrastructure.factories import (
    get_profile_analysis_point_warehouse,
    get_run_profile_analysis,
)
from src.modules.profile_analysis.infrastructure.persistence import (
    SQLAlchemyProfileAnalysisJobRepository,
)
from src.shared.db.session import SessionLocal
from src.shared.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.shared.workers.tasks.profile_analysis_tasks.generate_zone_profiles")
def generate_zone_profiles(
    request_id: str, zone_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Run profile generation asynchronously and return generated profile payload."""
    logger.info(
        "Profile analysis job started",
        extra={
            "request_id": request_id,
            "zone_id": zone_id,
            "payload_keys": sorted(payload.keys()),
        },
    )

    with SessionLocal() as db:
        persist_job = PersistProfileAnalysisJob(SQLAlchemyProfileAnalysisJobRepository(db))

        try:
            persist_job.mark_running(UUID(request_id))

            job_request = ProfileAnalysisJobRequest(
                request_id=UUID(request_id),
                zone_id=UUID(zone_id),
                payload=payload,
            )
            result = get_run_profile_analysis(db).execute(job_request)

            warehouse = get_profile_analysis_point_warehouse()
            with warehouse:
                PersistProfileAnalysisPoints(warehouse).execute(result)

            result_payload = {
                "request_id": str(result.request_id),
                "zone_id": str(result.zone_id),
                "provider": result.provider,
                "resolution_m": result.resolution_m,
                "transverse_profiles": len(result.transverse_profiles),
                "longitudinal_profiles": len(result.longitudinal_profiles),
                "total_points": result.total_points,
                "analytics_available": True,
            }
            persist_job.mark_completed(UUID(request_id), result_payload=result_payload)

            logger.info(
                "Profile analysis job completed",
                extra={
                    "request_id": request_id,
                    "zone_id": zone_id,
                    "total_points": result.total_points,
                    "transverse_profiles": len(result.transverse_profiles),
                    "longitudinal_profiles": len(result.longitudinal_profiles),
                },
            )

            return result_payload
        except Exception as exc:
            persist_job.mark_failed(UUID(request_id), error_message=str(exc))
            logger.exception(
                "Profile analysis job failed",
                extra={"request_id": request_id, "zone_id": zone_id},
            )
            raise
