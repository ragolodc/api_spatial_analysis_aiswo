from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from src.modules.profile_analysis.domain.entities import ProfileType
from src.modules.profile_analysis.infrastructure.factories import (
    get_get_profile_analysis_analytics,
    get_get_profile_analysis_job,
    get_get_profile_analysis_points,
    get_get_profile_analysis_summary,
    get_queue_profile_analysis,
)
from src.modules.profile_analysis.presentation.schemas import (
    ProfileAnalysisAnalyticsResponse,
    ProfileAnalysisJobAccepted,
    ProfileAnalysisJobResponse,
    ProfilePointRowResponse,
    ProfilePointsResponse,
    ProfileSummaryEntryResponse,
    ProfileSummaryResponse,
    QueueProfileAnalysisRequest,
)
from src.modules.profile_analysis.domain.entities import ProfileAnalysisJob
from src.shared.config import settings
from src.shared.db.session import get_db

_POINTS_MIN_LIMIT = 1
_POINTS_MAX_LIMIT = 10_000

router = APIRouter()


def _to_job_response(job: ProfileAnalysisJob) -> ProfileAnalysisJobResponse:
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


@router.get(
    "/processes/profile-analysis/jobs/{request_id}/points",
    response_model=ProfilePointsResponse,
    summary="Listar puntos muestreados de un job (paginado)",
    tags=["OGC Processes - Profile Analysis"],
)
def get_profile_analysis_points(
    request_id: UUID,
    profile_type: str | None = None,
    limit: int = 1000,
    offset: int = 0,
) -> ProfilePointsResponse:
    if limit < _POINTS_MIN_LIMIT or limit > _POINTS_MAX_LIMIT:
        raise HTTPException(status_code=400, detail=f"limit must be between {_POINTS_MIN_LIMIT} and {_POINTS_MAX_LIMIT}")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")
    if profile_type is not None and profile_type not in (ProfileType.TRANSVERSE, ProfileType.LONGITUDINAL):
        raise HTTPException(status_code=400, detail=f"profile_type must be one of: {', '.join(ProfileType)}")

    rows = get_get_profile_analysis_points().execute(
        request_id=request_id,
        profile_type=ProfileType(profile_type) if profile_type else None,
        limit=limit,
        offset=offset,
    )
    return ProfilePointsResponse(
        request_id=request_id,
        total=len(rows),
        limit=limit,
        offset=offset,
        items=[
            ProfilePointRowResponse(
                profile_type=r.profile_type,
                profile_key=r.profile_key,
                point_index=r.point_index,
                radius_m=r.radius_m,
                angle_deg=r.angle_deg,
                distance_m=r.distance_m,
                longitude=r.longitude,
                latitude=r.latitude,
                elevation_m=r.elevation_m,
            )
            for r in rows
        ],
    )


@router.get(
    "/processes/profile-analysis/jobs/{request_id}/summary",
    response_model=ProfileSummaryResponse,
    summary="Resumen por perfil (min/max/avg elevation agrupado por perfil)",
    tags=["OGC Processes - Profile Analysis"],
)
def get_profile_analysis_summary(request_id: UUID) -> ProfileSummaryResponse:
    entries = get_get_profile_analysis_summary().execute(request_id)
    return ProfileSummaryResponse(
        request_id=request_id,
        profiles=[
            ProfileSummaryEntryResponse(
                profile_type=e.profile_type,
                profile_key=e.profile_key,
                total_points=e.total_points,
                min_elevation_m=e.min_elevation_m,
                max_elevation_m=e.max_elevation_m,
                avg_elevation_m=e.avg_elevation_m,
            )
            for e in entries
        ],
    )
