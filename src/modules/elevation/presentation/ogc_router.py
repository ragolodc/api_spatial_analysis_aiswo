from fastapi import APIRouter, Depends, HTTPException

from src.modules.elevation.application.use_cases import GetHighestPointInPolygon, GetPointElevation
from src.modules.elevation.domain.exceptions import ElevationDataNotFound
from src.modules.elevation.domain.ports import ElevationProvider
from src.modules.elevation.domain.value_objects import GeoPoint, GeoPolygon
from src.modules.elevation.infrastructure.providers.planetary_computer import (
    PlanetaryComputerElevationProvider,
)
from src.modules.elevation.presentation.schemas import (
    ElevationFeature,
    HighestPointRequest,
    PointElevationRequest,
    PointGeometry,
)

router = APIRouter(prefix="/processes", tags=["OGC Processes"])


def get_elevation_provider() -> ElevationProvider:
    return PlanetaryComputerElevationProvider()


@router.post("/highest-point/execution", response_model=ElevationFeature)
def execute_highest_point(
    body: HighestPointRequest,
    provider: ElevationProvider = Depends(get_elevation_provider),
) -> ElevationFeature:
    try:
        polygon = GeoPolygon(coordinates=body.inputs.polygon.coordinates)
        point, elevation = GetHighestPointInPolygon(provider).execute(polygon)
    except ElevationDataNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return ElevationFeature(
        geometry=PointGeometry(coordinates=[point.longitude, point.latitude]),
        properties={"elevation_m": elevation.meters},
    )


@router.post("/point-elevation/execution", response_model=ElevationFeature)
def execute_point_elevation(
    body: PointElevationRequest,
    provider: ElevationProvider = Depends(get_elevation_provider),
) -> ElevationFeature:
    try:
        point = GeoPoint(
            longitude=body.inputs.point.coordinates[0],
            latitude=body.inputs.point.coordinates[1],
        )
        elevation = GetPointElevation(provider).execute(point)
    except ElevationDataNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return ElevationFeature(
        geometry=PointGeometry(coordinates=[point.longitude, point.latitude]),
        properties={"elevation_m": elevation.meters},
    )
