from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.modules.pivot_geometry_analysis.application.commands import QueueSlopeAnalysis
from src.modules.pivot_geometry_analysis.application.queries import (
    ComputeSlopeAnalysis,
    GetSlopeAnalysisJob,
    GetSlopeAnalysisResults,
)
from src.modules.pivot_geometry_analysis.infrastructure.factories import (
    get_compute_slope_analysis,
    get_get_slope_analysis_job,
    get_get_slope_analysis_results,
    get_queue_slope_analysis,
)
from src.modules.pivot_geometry_analysis.presentation.schemas import (
    ComputeCropClearanceRequest,
    ComputeLongitudinalSlopeRequest,
    ComputeSlopeAnalysisRequest,
    ComputeStructuralStressRequest,
    ComputeTorsionalSlopeRequest,
    ComputeTransversalSlopeRequest,
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


def _get_specific_analysis_result(
    request_id: UUID,
    use_case: GetSlopeAnalysisResults,
    section_key: str,
) -> SlopeAnalysisResultsResponse:
    result_payload = use_case.execute(request_id)
    if result_payload is None:
        raise HTTPException(
            status_code=404, detail="Slope analysis results not found or job not completed"
        )

    section_payload = result_payload.get(section_key)
    if section_payload is None:
        raise HTTPException(
            status_code=404,
            detail=f"Slope analysis section '{section_key}' not found for request",
        )

    return SlopeAnalysisResultsResponse(request_id=request_id, result_payload=section_payload)


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


@router.get(
    "/processes/slope-analysis/jobs/{request_id}/results/longitudinal-slope",
    response_model=SlopeAnalysisResultsResponse,
    summary="Obtener resultado específico de análisis longitudinal",
    tags=["OGC Processes - Slope Analysis"],
)
def get_longitudinal_slope_analysis_results(
    request_id: UUID,
    use_case: GetSlopeAnalysisResults = Depends(get_get_slope_analysis_results),
) -> SlopeAnalysisResultsResponse:
    return _get_specific_analysis_result(
        request_id=request_id,
        use_case=use_case,
        section_key="longitudinal_slope_analysis",
    )


@router.get(
    "/processes/slope-analysis/jobs/{request_id}/results/transversal-slope",
    response_model=SlopeAnalysisResultsResponse,
    summary="Obtener resultado específico de análisis transversal",
    tags=["OGC Processes - Slope Analysis"],
)
def get_transversal_slope_analysis_results(
    request_id: UUID,
    use_case: GetSlopeAnalysisResults = Depends(get_get_slope_analysis_results),
) -> SlopeAnalysisResultsResponse:
    return _get_specific_analysis_result(
        request_id=request_id,
        use_case=use_case,
        section_key="transversal_slope_analysis",
    )


@router.get(
    "/processes/slope-analysis/jobs/{request_id}/results/torsional-slope",
    response_model=SlopeAnalysisResultsResponse,
    summary="Obtener resultado específico de análisis torsional",
    tags=["OGC Processes - Slope Analysis"],
)
def get_torsional_slope_analysis_results(
    request_id: UUID,
    use_case: GetSlopeAnalysisResults = Depends(get_get_slope_analysis_results),
) -> SlopeAnalysisResultsResponse:
    return _get_specific_analysis_result(
        request_id=request_id,
        use_case=use_case,
        section_key="torsional_slope_analysis",
    )


@router.get(
    "/processes/slope-analysis/jobs/{request_id}/results/structural-stress",
    response_model=SlopeAnalysisResultsResponse,
    summary="Obtener resultado específico de análisis de estrés estructural",
    tags=["OGC Processes - Slope Analysis"],
)
def get_structural_stress_analysis_results(
    request_id: UUID,
    use_case: GetSlopeAnalysisResults = Depends(get_get_slope_analysis_results),
) -> SlopeAnalysisResultsResponse:
    return _get_specific_analysis_result(
        request_id=request_id,
        use_case=use_case,
        section_key="structural_stress_analysis",
    )


@router.get(
    "/processes/slope-analysis/jobs/{request_id}/results/crop-clearance",
    response_model=SlopeAnalysisResultsResponse,
    summary="Obtener resultado específico de análisis de clearance de cultivo",
    tags=["OGC Processes - Slope Analysis"],
)
def get_crop_clearance_analysis_results(
    request_id: UUID,
    use_case: GetSlopeAnalysisResults = Depends(get_get_slope_analysis_results),
) -> SlopeAnalysisResultsResponse:
    return _get_specific_analysis_result(
        request_id=request_id,
        use_case=use_case,
        section_key="crop_clearance_analysis",
    )


# ---------------------------------------------------------------------------
# Ephemeral compute endpoints (no persistence)
# ---------------------------------------------------------------------------


def _compute_and_get_section(
    body: Any,
    use_case: ComputeSlopeAnalysis,
    section_key: str | None,
) -> SlopeAnalysisResultsResponse:
    """Run computation and return either full payload or a single section."""
    try:
        payload = body.model_dump(mode="json")
        result = use_case.execute(
            profile_analysis_id=body.inputs.profile_analysis_id,
            payload=payload,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if section_key is None:
        return SlopeAnalysisResultsResponse(request_id=result["request_id"], result_payload=result)

    section = result.get(section_key)
    if section is None:
        raise HTTPException(
            status_code=404, detail=f"Section '{section_key}' not found in computation result"
        )
    return SlopeAnalysisResultsResponse(request_id=result["request_id"], result_payload=section)


@router.post(
    "/processes/slope-analysis/compute",
    response_model=SlopeAnalysisResultsResponse,
    summary="Calcular análisis de pendientes sin persistir (todos los análisis)",
    tags=["OGC Processes - Slope Analysis"],
)
def compute_slope_analysis(
    body: ComputeSlopeAnalysisRequest,
    use_case: ComputeSlopeAnalysis = Depends(get_compute_slope_analysis),
) -> SlopeAnalysisResultsResponse:
    return _compute_and_get_section(body, use_case, section_key=None)


@router.post(
    "/processes/slope-analysis/compute/longitudinal-slope",
    response_model=SlopeAnalysisResultsResponse,
    summary="Calcular análisis de pendiente longitudinal sin persistir",
    tags=["OGC Processes - Slope Analysis"],
)
def compute_longitudinal_slope(
    body: ComputeLongitudinalSlopeRequest,
    use_case: ComputeSlopeAnalysis = Depends(get_compute_slope_analysis),
) -> SlopeAnalysisResultsResponse:
    return _compute_and_get_section(body, use_case, section_key="longitudinal_slope_analysis")


@router.post(
    "/processes/slope-analysis/compute/transversal-slope",
    response_model=SlopeAnalysisResultsResponse,
    summary="Calcular análisis de pendiente transversal sin persistir",
    tags=["OGC Processes - Slope Analysis"],
)
def compute_transversal_slope(
    body: ComputeTransversalSlopeRequest,
    use_case: ComputeSlopeAnalysis = Depends(get_compute_slope_analysis),
) -> SlopeAnalysisResultsResponse:
    return _compute_and_get_section(body, use_case, section_key="transversal_slope_analysis")


@router.post(
    "/processes/slope-analysis/compute/torsional-slope",
    response_model=SlopeAnalysisResultsResponse,
    summary="Calcular análisis de pendiente torsional sin persistir",
    tags=["OGC Processes - Slope Analysis"],
)
def compute_torsional_slope(
    body: ComputeTorsionalSlopeRequest,
    use_case: ComputeSlopeAnalysis = Depends(get_compute_slope_analysis),
) -> SlopeAnalysisResultsResponse:
    return _compute_and_get_section(body, use_case, section_key="torsional_slope_analysis")


@router.post(
    "/processes/slope-analysis/compute/structural-stress",
    response_model=SlopeAnalysisResultsResponse,
    summary="Calcular análisis de estrés estructural sin persistir",
    tags=["OGC Processes - Slope Analysis"],
)
def compute_structural_stress(
    body: ComputeStructuralStressRequest,
    use_case: ComputeSlopeAnalysis = Depends(get_compute_slope_analysis),
) -> SlopeAnalysisResultsResponse:
    return _compute_and_get_section(body, use_case, section_key="structural_stress_analysis")


@router.post(
    "/processes/slope-analysis/compute/crop-clearance",
    response_model=SlopeAnalysisResultsResponse,
    summary="Calcular análisis de clearance de cultivo sin persistir",
    tags=["OGC Processes - Slope Analysis"],
)
def compute_crop_clearance(
    body: ComputeCropClearanceRequest,
    use_case: ComputeSlopeAnalysis = Depends(get_compute_slope_analysis),
) -> SlopeAnalysisResultsResponse:
    return _compute_and_get_section(body, use_case, section_key="crop_clearance_analysis")
