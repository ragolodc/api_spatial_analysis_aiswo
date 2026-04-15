from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.modules.elevation_analysis.application import (
    GenerateZoneContours,
    GetZoneContours,
    ListZoneAnalyses,
    RunZoneElevationAnalysis,
)
from src.modules.elevation_analysis.domain.exceptions import (
    ContoursGenerationError,
    DemNotAvailable,
    ElevationAnalysisException,
    ZoneNotFound,
)
from src.modules.elevation_analysis.infrastructure.factories import (
    get_generate_zone_contours,
    get_get_zone_contours,
    get_list_zone_analyses,
    get_run_zone_elevation_analysis,
)
from src.modules.elevation_analysis.presentation.schemas import (
    AnalysisProperties,
    ContourProperties,
    ElevationAnalysisCollection,
    ElevationAnalysisFeature,
    ElevationContourCollection,
    ElevationContourFeature,
    ElevationPointFeature,
    ElevationPointProperties,
    GenerateContoursRequest,
    MultiLineStringGeometry,
    PointGeometry,
    RunAnalysisRequest,
)
from src.shared.db.session import get_db

router = APIRouter(tags=["Elevation Analysis"])


# ---------------------------------------------------------------------------
# OGC Processes — ejecutar análisis y generar curvas
# ---------------------------------------------------------------------------


@router.post(
    "/processes/zone-elevation-analysis/execution",
    response_model=ElevationAnalysisFeature,
    summary="Analizar elevación de una zona y persistir puntos característicos",
)
def run_zone_elevation_analysis(
    body: RunAnalysisRequest,
    db: Session = Depends(get_db),
) -> ElevationAnalysisFeature:
    try:
        command = get_run_zone_elevation_analysis(db)
        analysis = command.execute(zone_id=body.inputs.zone_id)
    except ZoneNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DemNotAvailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ElevationAnalysisException as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _analysis_to_feature(analysis)


@router.post(
    "/processes/zone-contours/execution",
    response_model=ElevationContourCollection,
    summary="Generar y persistir curvas de nivel para una zona",
)
def generate_zone_contours(
    body: GenerateContoursRequest,
    db: Session = Depends(get_db),
) -> ElevationContourCollection:
    try:
        command = get_generate_zone_contours(db)
        contours = command.execute(
            zone_id=body.inputs.zone_id,
            interval_m=body.inputs.interval_m,
        )
    except ZoneNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ContoursGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ElevationAnalysisException as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _contours_to_collection(contours)


# ---------------------------------------------------------------------------
# OGC Features — consultar resultados persistidos
# ---------------------------------------------------------------------------


@router.get(
    "/collections/zones/{zone_id}/analyses",
    response_model=ElevationAnalysisCollection,
    summary="Listar análisis de elevación de una zona",
)
def list_zone_analyses(
    zone_id: str,
    db: Session = Depends(get_db),
) -> ElevationAnalysisCollection:
    query = get_list_zone_analyses(db)
    analyses = query.execute(UUID(zone_id))

    return ElevationAnalysisCollection(
        features=[_analysis_to_feature(a) for a in analyses],
        number_matched=len(analyses),
    )


@router.get(
    "/collections/zones/{zone_id}/contours",
    response_model=ElevationContourCollection,
    summary="Obtener curvas de nivel de una zona",
)
def get_zone_contours(
    zone_id: str,
    db: Session = Depends(get_db),
) -> ElevationContourCollection:
    query = get_get_zone_contours(db)
    contours = query.execute(UUID(zone_id))

    return _contours_to_collection(contours)


# ---------------------------------------------------------------------------
# Helpers de mapeo dominio → schema OGC
# ---------------------------------------------------------------------------

def _analysis_to_feature(analysis) -> ElevationAnalysisFeature:
    points = [
        ElevationPointFeature(
            id=str(p.id),
            geometry=PointGeometry(coordinates=[p.longitude, p.latitude]),
            properties=ElevationPointProperties(
                point_type=p.point_type,
                elevation_m=p.elevation_m,
                analysis_id=p.analysis_id,
            ),
        )
        for p in analysis.points
    ]
    return ElevationAnalysisFeature(
        id=str(analysis.id),
        properties=AnalysisProperties(
            zone_id=analysis.zone_id,
            provider=analysis.provider,
            resolution_m=analysis.resolution_m,
            analyzed_at=analysis.analyzed_at.isoformat(),
        ),
        characteristic_points=points,
    )


def _contours_to_collection(contours) -> ElevationContourCollection:
    features = [
        ElevationContourFeature(
            id=str(c.id),
            geometry=MultiLineStringGeometry(coordinates=c.geometry["coordinates"]),
            properties=ContourProperties(
                zone_id=c.zone_id,
                elevation_m=c.elevation_m,
                interval_m=c.interval_m,
                provider=c.provider,
                generated_at=c.generated_at.isoformat(),
            ),
        )
        for c in contours
    ]
    return ElevationContourCollection(features=features, number_matched=len(features))
