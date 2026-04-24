from fastapi import APIRouter, Depends, HTTPException

from src.modules.pivot_geometry_analysis.infrastructure.factories import get_queue_slope_analysis
from src.modules.pivot_geometry_analysis.presentation.schemas import (
    QueueSlopeAnalysisRequest,
    SlopeAnalysisJobAccepted,
)
from src.shared.config import settings

router = APIRouter()


@router.post(
    "/processes/slope-analysis/execution",
    response_model=SlopeAnalysisJobAccepted,
    summary="Encolar análisis de pendientes para una zona",
    tags=["OGC Processes - Slope Analysis"],
    status_code=202,
)
def queue_slope_analysis(
    body: QueueSlopeAnalysisRequest, use_case=Depends(get_queue_slope_analysis)
) -> dict[str, str]:
    try:
        payload = body.model_dump(mode="json")
        request_id = use_case.execute(zone_id=body.inputs.zone_id, payload=payload)

    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return SlopeAnalysisJobAccepted(
        request_id=request_id, status="queued", queue=settings.slope_analysis_queue
    )
