"""OGC API Processes endpoints for profile-analysis jobs."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from src.modules.profile_analysis.infrastructure.factories import (
    get_get_profile_analysis_analytics,
    get_get_profile_analysis_job,
    get_queue_profile_analysis,
)
from src.modules.profile_analysis.presentation.schemas import (
    ProfileAnalysisAnalyticsResponse,
    ProfileAnalysisJobAccepted,
    ProfileAnalysisJobResponse,
    QueueProfileAnalysisRequest,
)
from src.shared.config import settings
from src.shared.db.session import get_db

router = APIRouter()


def _to_job_response(job) -> ProfileAnalysisJobResponse:
    return ProfileAnalysisJobResponse(
        request_id=job.request_id,
        zone_id=job.zone_id,
        status=job.status.value,
        error_message=job.error_message,
        queued_at=job.queued_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        result_payload=job.result_payload,
    )


@router.post(
    "/processes/profile-analysis/execution",
    response_model=ProfileAnalysisJobAccepted,
    summary="Encolar analisis de perfiles para una zona",
    tags=["OGC Processes - Profile Analysis"],
    status_code=202,
)
def queue_profile_analysis(
    body: QueueProfileAnalysisRequest,
    db: Session = Depends(get_db),
) -> ProfileAnalysisJobAccepted:
    max_points = settings.profile_analysis_max_points
    if body.inputs.estimated_points and body.inputs.estimated_points > max_points:
        raise HTTPException(
            status_code=400,
            detail=f"estimated_points exceeds configured limit ({max_points})",
        )

    payload = body.model_dump(mode="json")
    request_id = get_queue_profile_analysis(db).execute(
        zone_id=body.inputs.zone_id,
        payload=payload,
    )
    return ProfileAnalysisJobAccepted(
        request_id=request_id,
        status="queued",
        queue=settings.profile_analysis_queue,
    )


@router.get(
    "/processes/profile-analysis/jobs/{request_id}",
    response_model=ProfileAnalysisJobResponse,
    summary="Consultar estado de un job de analisis de perfiles",
    tags=["OGC Processes - Profile Analysis"],
)
def get_profile_analysis_job(
    request_id: UUID,
    db: Session = Depends(get_db),
) -> ProfileAnalysisJobResponse:
    job = get_get_profile_analysis_job(db).execute(request_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Profile analysis job not found")
    return _to_job_response(job)


@router.get(
    "/processes/profile-analysis/jobs/{request_id}/analytics",
    response_model=ProfileAnalysisAnalyticsResponse,
    summary="Consultar agregados analiticos de un job de analisis de perfiles",
    tags=["OGC Processes - Profile Analysis"],
)
def get_profile_analysis_analytics(request_id: UUID) -> ProfileAnalysisAnalyticsResponse:
    analytics = get_get_profile_analysis_analytics().execute(request_id)
    if analytics is None:
        raise HTTPException(status_code=404, detail="Profile analysis analytics not found")
    return ProfileAnalysisAnalyticsResponse(
        request_id=analytics.request_id,
        total_points=analytics.total_points,
        min_elevation_m=analytics.min_elevation_m,
        max_elevation_m=analytics.max_elevation_m,
        avg_elevation_m=analytics.avg_elevation_m,
    )
