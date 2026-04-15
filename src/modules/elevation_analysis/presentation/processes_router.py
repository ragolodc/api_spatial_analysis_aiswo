"""OGC API Processes endpoints for elevation analysis."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.modules.elevation_analysis.domain.exceptions import (
    DemNotAvailable,
    ElevationAnalysisException,
    ZoneNotFound,
)
from src.modules.elevation_analysis.infrastructure.factories import (
    get_generate_zone_contours,
    get_run_zone_elevation_analysis,
)
from src.modules.elevation_analysis.presentation._mappers import (
    analysis_to_feature,
    contours_to_collection,
)
from src.modules.elevation_analysis.presentation.schemas import (
    ElevationAnalysisFeature,
    ElevationContourCollection,
    GenerateContoursRequest,
    RunAnalysisRequest,
)
from src.shared.db.session import get_db

router = APIRouter()


@router.post(
    "/processes/analyze-zone-elevation/execution",
    response_model=ElevationAnalysisFeature,
    summary="Analizar elevación de una zona y persistir puntos característicos",
    tags=["OGC Processes - Zone Analysis"],
)
def run_zone_elevation_analysis(
    body: RunAnalysisRequest,
    db: Session = Depends(get_db),
) -> ElevationAnalysisFeature:
    try:
        analysis = get_run_zone_elevation_analysis(db).execute(zone_id=body.inputs.zone_id)
    except ZoneNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DemNotAvailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ElevationAnalysisException as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return analysis_to_feature(analysis)


@router.post(
    "/processes/generate-zone-contours/execution",
    response_model=ElevationContourCollection,
    summary="Generar y persistir curvas de nivel para una zona",
    tags=["OGC Processes - Zone Analysis"],
)
def generate_zone_contours(
    body: GenerateContoursRequest,
    db: Session = Depends(get_db),
) -> ElevationContourCollection:
    try:
        contours = get_generate_zone_contours(db).execute(
            zone_id=body.inputs.zone_id,
            interval_m=body.inputs.interval_m,
        )
    except ZoneNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DemNotAvailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ElevationAnalysisException as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return contours_to_collection(contours)
