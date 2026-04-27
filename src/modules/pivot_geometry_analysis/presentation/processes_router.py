from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.modules.pivot_geometry_analysis.infrastructure.factories import get_queue_slope_analysis
from src.modules.pivot_geometry_analysis.presentation.schemas import (
    QueueSlopeAnalysisRequest,
    SlopeAnalysisJobAccepted,
)
from src.shared.config import settings
from src.shared.db.session import get_db

router = APIRouter()


@router.post(
    "/processes/slope-analysis/execution",
    response_model=SlopeAnalysisJobAccepted,
    summary="Encolar análisis de pendientes para una zona",
    tags=["OGC Processes - Slope Analysis"],
    status_code=202,
)
def queue_slope_analysis(
    body: QueueSlopeAnalysisRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        use_case = get_queue_slope_analysis(db)
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
