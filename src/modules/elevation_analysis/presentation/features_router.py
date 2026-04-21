"""OGC API Features endpoints for elevation analysis collections."""

from uuid import UUID

from fastapi import APIRouter, Depends

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

router = APIRouter()


@router.get(
    "/collections/zone-analyses/items",
    response_model=ElevationAnalysisCollection,
    summary="Listar análisis de elevación de una zona",
    tags=["OGC Features - Zone Analyses"],
)
def list_zone_analyses(
    zone_id: UUID,
    use_case=Depends(get_list_zone_analyses),
) -> ElevationAnalysisCollection:
    analyses = use_case.execute(zone_id)
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
    use_case=Depends(get_get_zone_contours),
) -> ElevationContourCollection:
    contours = use_case.execute(zone_id)
    return contours_to_collection(contours)
