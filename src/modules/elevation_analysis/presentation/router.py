from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.modules.elevation_analysis.application.use_cases import (
    GenerateZoneContours,
    GetZoneAnalyses,
    GetZoneContours,
    RunZoneElevationAnalysis,
)
from src.modules.elevation_analysis.domain.ports import ElevationAnalysisProvider
from src.modules.elevation_analysis.infrastructure.persistence.repository import (
    SQLAlchemyElevationAnalysisRepository,
    SQLAlchemyElevationContourRepository,
)
from src.modules.elevation_analysis.infrastructure.providers.planetary_computer import (
    PlanetaryComputerAnalysisProvider,
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
from src.modules.zones.infrastructure.persistence.repository import SQLAlchemyZoneRepository
from src.shared.db.session import get_db

router = APIRouter(tags=["Elevation Analysis"])


def _get_provider() -> ElevationAnalysisProvider:
    return PlanetaryComputerAnalysisProvider()


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
    provider: ElevationAnalysisProvider = Depends(_get_provider),
) -> ElevationAnalysisFeature:
    zone_repo = SQLAlchemyZoneRepository(db)
    analysis_repo = SQLAlchemyElevationAnalysisRepository(db)

    try:
        analysis = RunZoneElevationAnalysis(provider, analysis_repo, zone_repo).execute(
            zone_id=body.inputs.zone_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return _analysis_to_feature(analysis)


@router.post(
    "/processes/zone-contours/execution",
    response_model=ElevationContourCollection,
    summary="Generar y persistir curvas de nivel para una zona",
)
def generate_zone_contours(
    body: GenerateContoursRequest,
    db: Session = Depends(get_db),
    provider: ElevationAnalysisProvider = Depends(_get_provider),
) -> ElevationContourCollection:
    zone_repo = SQLAlchemyZoneRepository(db)
    contour_repo = SQLAlchemyElevationContourRepository(db)

    try:
        contours = GenerateZoneContours(provider, contour_repo, zone_repo).execute(
            zone_id=body.inputs.zone_id,
            interval_m=body.inputs.interval_m,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

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
    from uuid import UUID

    analysis_repo = SQLAlchemyElevationAnalysisRepository(db)
    analyses = GetZoneAnalyses(analysis_repo).execute(UUID(zone_id))

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
    from uuid import UUID

    contour_repo = SQLAlchemyElevationContourRepository(db)
    contours = GetZoneContours(contour_repo).execute(UUID(zone_id))

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
