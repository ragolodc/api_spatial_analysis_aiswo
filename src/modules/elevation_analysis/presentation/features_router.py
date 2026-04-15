"""OGC API Features endpoints for elevation analysis collections."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.modules.elevation_analysis.infrastructure.factories import (
    get_get_zone_contours,
    get_list_zone_analyses,
)
from src.modules.elevation_analysis.presentation._mappers import (
    analysis_to_feature,
    contours_to_collection,
)
from src.modules.elevation_analysis.presentation.schemas import (
    ElevationAnalysisCollection,
    ElevationContourCollection,
)
from src.shared.db.session import get_db

router = APIRouter()


@router.get(
    "/collections/zone-analyses/items",
    response_model=ElevationAnalysisCollection,
    summary="Listar análisis de elevación de una zona",
    tags=["OGC Features - Zone Analyses"],
)
def list_zone_analyses(
    zone_id: UUID,
    db: Session = Depends(get_db),
) -> ElevationAnalysisCollection:
    analyses = get_list_zone_analyses(db).execute(zone_id)
    return ElevationAnalysisCollection(
        features=[analysis_to_feature(a) for a in analyses],
        number_matched=len(analyses),
    )


@router.get(
    "/collections/zone-contours/items",
    response_model=ElevationContourCollection,
    summary="Obtener curvas de nivel de una zona",
    tags=["OGC Features - Zone Contours"],
)
def get_zone_contours(
    zone_id: UUID,
    db: Session = Depends(get_db),
) -> ElevationContourCollection:
    contours = get_get_zone_contours(db).execute(zone_id)
    return contours_to_collection(contours)
