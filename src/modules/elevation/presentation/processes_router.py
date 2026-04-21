from fastapi import APIRouter, Depends, HTTPException

from src.modules.elevation.domain.exceptions import (
    ElevationDataNotFound,
)
from src.modules.elevation.domain.value_objects import GeoPoint
from src.modules.elevation.infrastructure.factories import (
    get_get_highest_point,
    get_get_point_elevation,
    get_zone_geometry_reader,
)
from src.modules.elevation.presentation.schemas import (
    ElevationFeature,
    HighestPointRequest,
    PointElevationRequest,
    PointGeometry,
)
from src.shared.domain import GeoPolygon
from src.shared.domain.exceptions import ElevationSourceNotConfigured

router = APIRouter(prefix="/processes", tags=["OGC Processes - Elevation Queries"])


@router.post("/highest-point/execution", response_model=ElevationFeature)
def execute_highest_point(
    body: HighestPointRequest,
    use_case=Depends(get_get_highest_point),
    zone_reader=Depends(get_zone_geometry_reader),
) -> ElevationFeature:
    try:
        if body.inputs.polygon:
            polygon = GeoPolygon(coordinates=body.inputs.polygon.coordinates)
        else:
            polygon = zone_reader.find_polygon(body.inputs.zone_id)
            if not polygon:
                raise HTTPException(status_code=404, detail="Zone not found")
        point, elevation = use_case.execute(polygon)
    except ElevationSourceNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ElevationDataNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ElevationFeature(
        geometry=PointGeometry(coordinates=[point.longitude, point.latitude]),
        properties={"elevation_m": elevation.meters},
    )


@router.post("/point-elevation/execution", response_model=ElevationFeature)
def execute_point_elevation(
    body: PointElevationRequest,
    use_case=Depends(get_get_point_elevation),
) -> ElevationFeature:
    try:
        point = GeoPoint(
            longitude=body.inputs.point.coordinates[0],
            latitude=body.inputs.point.coordinates[1],
        )
        elevation = use_case.execute(point)
    except ElevationSourceNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ElevationDataNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ElevationFeature(
        geometry=PointGeometry(coordinates=[point.longitude, point.latitude]),
        properties={"elevation_m": elevation.meters},
    )
