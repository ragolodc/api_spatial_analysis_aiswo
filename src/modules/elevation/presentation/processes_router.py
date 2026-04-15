from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.modules.elevation.domain.exceptions import ElevationDataNotFound
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
from src.shared.db.session import get_db
from src.shared.domain import GeoPolygon

router = APIRouter(prefix="/processes", tags=["OGC Processes - Elevation Queries"])


@router.post("/highest-point/execution", response_model=ElevationFeature)
def execute_highest_point(
    body: HighestPointRequest,
    db: Session = Depends(get_db),
) -> ElevationFeature:
    try:
        if body.inputs.polygon:
            polygon = GeoPolygon(coordinates=body.inputs.polygon.coordinates)
        else:
            polygon = get_zone_geometry_reader(db).find_polygon(body.inputs.zone_id)
            if not polygon:
                raise HTTPException(status_code=404, detail="Zone not found")
        point, elevation = get_get_highest_point(db).execute(polygon)
    except ElevationDataNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return ElevationFeature(
        geometry=PointGeometry(coordinates=[point.longitude, point.latitude]),
        properties={"elevation_m": elevation.meters},
    )


@router.post("/point-elevation/execution", response_model=ElevationFeature)
def execute_point_elevation(
    body: PointElevationRequest,
    db: Session = Depends(get_db),
) -> ElevationFeature:
    try:
        point = GeoPoint(
            longitude=body.inputs.point.coordinates[0],
            latitude=body.inputs.point.coordinates[1],
        )
        elevation = get_get_point_elevation(db).execute(point)
    except ElevationDataNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return ElevationFeature(
        geometry=PointGeometry(coordinates=[point.longitude, point.latitude]),
        properties={"elevation_m": elevation.meters},
    )
