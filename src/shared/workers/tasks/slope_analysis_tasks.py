import logging
from typing import Any
from uuid import UUID

from src.modules.pivot_geometry_analysis.application.commands import (
    PersistSlopeAnalysis,
    PersistSlopeAnalysisJob,
)
from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJobRequest,
)
from src.modules.pivot_geometry_analysis.infrastructure.factories import (
    get_run_slope_analysis,
    get_slope_analysis_warehouse,
)
from src.modules.pivot_geometry_analysis.infrastructure.persistence import (
    SQLAlchemySlopeAnalysisJobRepository,
)
from src.shared.db.session import SessionLocal
from src.shared.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.shared.workers.tasks.slope_analysis_tasks.generate_slope_analysis")
def generate_slope_analysis(
    request_id: UUID, zone_id: UUID, profile_analysis_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """Run slope generation asynchronously and return generated slope payload."""
    logger.info(
        "Slope analysis job started",
        extra={
            "request_id": request_id,
            "zone_id": zone_id,
            "profile_analysis_id": profile_analysis_id,
            "payload_keys": sorted(payload.keys()),
        },
    )

    with SessionLocal() as db:
        persist_job = PersistSlopeAnalysisJob(repository=SQLAlchemySlopeAnalysisJobRepository(db))
        try:
            persist_job.mark_running(request_id=request_id)
            job_request = SlopeAnalysisJobRequest(
                request_id=request_id,
                zone_id=zone_id,
                profile_analysis_id=profile_analysis_id,
                payload=payload,
            )
            result = get_run_slope_analysis(db=db).execute(request=job_request)

            warehouse = get_slope_analysis_warehouse()
            with warehouse:
                PersistSlopeAnalysis(warehouse).execute(result, job_request)

            result_payload = {
                "request_id": str(result.request_id),
                "longitudinal_slope_analysis": str(result.longitudinal_slope_analysis.request_id),
                "transversal_slope_analysis": str(result.transversal_slope_analysis.request_id),
                "torsional_slope_analysis": str(result.torsional_slope_analysis.request_id),
                "structural_stress_analysis": str(result.structural_stress_analysis.request_id),
                "crop_clearance_analysis": str(result.crop_clearance_analysis.request_id),
            }
            persist_job.mark_completed(UUID(request_id), result_payload=result_payload)

            logger.info(
                "Profile analysis job completed",
                extra={
                    "request_id": str(result.request_id),
                    "longitudinal_slope_analysis": str(
                        result.longitudinal_slope_analysis.request_id
                    ),
                    "transversal_slope_analysis": str(result.transversal_slope_analysis.request_id),
                    "torsional_slope_analysis": str(result.torsional_slope_analysis.request_id),
                    "structural_stress_analysis": str(result.structural_stress_analysis.request_id),
                    "crop_clearance_analysis": str(result.crop_clearance_analysis.request_id),
                },
            )
        except Exception as exc:
            persist_job.mark_failed(request_id, error_message=str(exc))
            logger.exception(
                "Slope analysis job failed",
                extra={"request_id": request_id, "zone_id": zone_id},
            )
