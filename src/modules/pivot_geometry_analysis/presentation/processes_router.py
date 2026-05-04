from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.modules.pivot_geometry_analysis.application.commands import QueueSlopeAnalysis
from src.modules.pivot_geometry_analysis.application.queries import (
    GetSlopeAnalysisJob,
    GetSlopeAnalysisResults,
)
from src.modules.pivot_geometry_analysis.infrastructure.factories import (
    get_get_slope_analysis_job,
    get_get_slope_analysis_results,
    get_queue_slope_analysis,
)
from src.modules.pivot_geometry_analysis.presentation.schemas import (
    QueueSlopeAnalysisRequest,
    SlopeAnalysisJobAccepted,
    SlopeAnalysisJobResponse,
    SlopeAnalysisResultsResponse,
)
from src.shared.config import settings

router = APIRouter()


def _count_nested_items(payload: dict[str, Any], key: str, item_key: str) -> int | None:
    section = payload.get(key)
    if not isinstance(section, dict):
        return None
    items = section.get(item_key)
    if not isinstance(items, list):
        return None
    return len(items)


def _to_job_summary_payload(job) -> dict[str, Any] | None:
    payload = job.result_payload
    if payload is None:
        return None

    if {
        "longitudinal_spans",
        "transversal_points",
        "torsional_spans",
        "structural_nodes",
        "structural_runs",
        "crop_clearance_points",
    }.issubset(payload.keys()):
        # Already summarized payload (new contract)
        return payload

    # Legacy payloads are normalized to summary to keep /jobs/{id} consistent.
    longitudinal_spans = _count_nested_items(payload, "longitudinal_slope_analysis", "spans")
    transversal_points = _count_nested_items(payload, "transversal_slope_analysis", "points")
    torsional_spans = _count_nested_items(payload, "torsional_slope_analysis", "spans")
    structural_nodes = _count_nested_items(payload, "structural_stress_analysis", "nodes")
    structural_runs = _count_nested_items(payload, "structural_stress_analysis", "runs")
    crop_clearance_points = _count_nested_items(payload, "crop_clearance_analysis", "points")

    return {
        "request_id": str(job.request_id),
        "zone_id": str(job.zone_id),
        "profile_analysis_id": str(job.profile_analysis_id),
        "longitudinal_spans": longitudinal_spans,
        "transversal_points": transversal_points,
        "torsional_spans": torsional_spans,
        "structural_nodes": structural_nodes,
        "structural_runs": structural_runs,
        "crop_clearance_points": crop_clearance_points,
        "analytics_available": any(
            v is not None
            for v in [
                longitudinal_spans,
                transversal_points,
                torsional_spans,
                structural_nodes,
                structural_runs,
                crop_clearance_points,
            ]
        ),
    }


def _to_job_response(job) -> SlopeAnalysisJobResponse:
    """Convert SlopeAnalysisJob entity to response schema."""
    return SlopeAnalysisJobResponse(
        request_id=job.request_id,
        zone_id=job.zone_id,
        status=job.status.value,
        error_message=job.error_message,
        queued_at=job.queued_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        result_payload=_to_job_summary_payload(job),
    )


@router.post(
    "/processes/slope-analysis/execution",
    response_model=SlopeAnalysisJobAccepted,
    summary="Encolar análisis de pendientes para una zona",
    tags=["OGC Processes - Slope Analysis"],
    status_code=202,
)
def queue_slope_analysis(
    body: QueueSlopeAnalysisRequest,
    use_case: QueueSlopeAnalysis = Depends(get_queue_slope_analysis),
) -> SlopeAnalysisJobAccepted:
    try:
        payload = body.model_dump(mode="json")
        request_id = use_case.execute(
            zone_id=body.inputs.zone_id,
            profile_analysis_id=body.inputs.profile_analysis_id,
            payload=payload,
        )

    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return SlopeAnalysisJobAccepted(
        request_id=request_id, status="queued", queue=settings.slope_analysis_queue
    )


@router.get(
    "/processes/slope-analysis/jobs/{request_id}",
    response_model=SlopeAnalysisJobResponse,
    summary="Consultar estado de un job de análisis de pendientes",
    tags=["OGC Processes - Slope Analysis"],
)
def get_slope_analysis_job(
    request_id: UUID,
    use_case: GetSlopeAnalysisJob = Depends(get_get_slope_analysis_job),
) -> SlopeAnalysisJobResponse:
    job = use_case.execute(request_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Slope analysis job not found")
    return _to_job_response(job)


@router.get(
    "/processes/slope-analysis/jobs/{request_id}/results",
    response_model=SlopeAnalysisResultsResponse,
    summary="Obtener resultados de un análisis de pendientes completado",
    tags=["OGC Processes - Slope Analysis"],
)
def get_slope_analysis_results(
    request_id: UUID,
    use_case: GetSlopeAnalysisResults = Depends(get_get_slope_analysis_results),
) -> SlopeAnalysisResultsResponse:
    result_payload = use_case.execute(request_id)
    if result_payload is None:
        raise HTTPException(
            status_code=404, detail="Slope analysis results not found or job not completed"
        )
    return SlopeAnalysisResultsResponse(request_id=request_id, result_payload=result_payload)
