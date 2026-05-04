from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError

from src.modules.profile_analysis.application import GetProfileAnalysisPoints
from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisJob,
    ProfilePointFilters,
    ProfileType,
)
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
    ProfileAnalysisPointFiltersQuery,
    ProfilePointRowResponse,
    ProfilePointsResponse,
    ProfileSummaryEntryResponse,
    ProfileSummaryResponse,
    QueueProfileAnalysisRequest,
)
from src.shared.config import settings
from src.shared.domain import ElevationSourceNotConfigured

_POINTS_MIN_LIMIT = 1
_POINTS_MAX_LIMIT = 10_000

router = APIRouter()


def _resolve_profile_analysis_point_filters(
    profile_key: str | None = Query(default=None),
    min_distance_m: float | None = Query(default=None, ge=0),
    max_distance_m: float | None = Query(default=None, ge=0),
    min_elevation_m: float | None = Query(default=None),
    max_elevation_m: float | None = Query(default=None),
) -> ProfileAnalysisPointFiltersQuery:
    try:
        return ProfileAnalysisPointFiltersQuery(
            profile_key=profile_key,
            min_distance_m=min_distance_m,
            max_distance_m=max_distance_m,
            min_elevation_m=min_elevation_m,
            max_elevation_m=max_elevation_m,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


def _resolve_get_profile_analysis_points_use_case() -> Callable[[], GetProfileAnalysisPoints]:
    return get_get_profile_analysis_points


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
    use_case=Depends(get_queue_profile_analysis),
) -> ProfileAnalysisJobAccepted:
    try:
        max_points = settings.profile_analysis_max_points
        if body.inputs.estimated_points and body.inputs.estimated_points > max_points:
            raise HTTPException(
                status_code=400,
                detail=f"estimated_points exceeds configured limit ({max_points})",
            )

        payload = body.model_dump(mode="json")
        request_id = use_case.execute(
            zone_id=body.inputs.zone_id,
            payload=payload,
        )
    except ElevationSourceNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
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
    use_case=Depends(get_get_profile_analysis_job),
) -> ProfileAnalysisJobResponse:
    job = use_case.execute(request_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Profile analysis job not found")
    return _to_job_response(job)


@router.get(
    "/processes/profile-analysis/jobs/{request_id}/analytics",
    response_model=ProfileAnalysisAnalyticsResponse,
    summary="Consultar agregados analiticos de un job de analisis de perfiles",
    tags=["OGC Processes - Profile Analysis"],
)
def get_profile_analysis_analytics(
    request_id: UUID,
    use_case=Depends(get_get_profile_analysis_analytics),
) -> ProfileAnalysisAnalyticsResponse:
    analytics = use_case.execute(request_id)
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
    use_case_factory: Callable[[], GetProfileAnalysisPoints] = Depends(
        _resolve_get_profile_analysis_points_use_case
    ),
    filters: ProfileAnalysisPointFiltersQuery = Depends(_resolve_profile_analysis_point_filters),
    profile_type: ProfileType | None = None,
    limit: int = Query(default=1000, ge=_POINTS_MIN_LIMIT, le=_POINTS_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> ProfilePointsResponse:
    use_case: GetProfileAnalysisPoints = use_case_factory()
    rows = use_case.execute(
        request_id=request_id,
        profile_type=profile_type,
        filters=ProfilePointFilters(
            profile_key=filters.profile_key,
            min_distance_m=filters.min_distance_m,
            max_distance_m=filters.max_distance_m,
            min_elevation_m=filters.min_elevation_m,
            max_elevation_m=filters.max_elevation_m,
        ),
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
def get_profile_analysis_summary(
    request_id: UUID,
    use_case=Depends(get_get_profile_analysis_summary),
) -> ProfileSummaryResponse:
    entries = use_case.execute(request_id)
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
