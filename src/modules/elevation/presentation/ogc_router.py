from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.modules.elevation.application import GetHighestPointInPolygon, GetPointElevation
from src.modules.elevation.domain.exceptions import ElevationDataNotFound
from src.modules.elevation.domain.value_objects import GeoPoint, GeoPolygon
from src.modules.elevation.infrastructure.factories import (
    get_get_highest_point,
    get_get_point_elevation,
)
from src.modules.elevation.presentation.schemas import (
    ElevationFeature,
    HighestPointRequest,
    PointElevationRequest,
    PointGeometry,
)
from src.modules.zones.infrastructure.persistence import SQLAlchemyZoneRepository
from src.shared.db.session import get_db

router = APIRouter(prefix="/processes", tags=["OGC Processes"])



@router.post("/highest-point/execution", response_model=ElevationFeature)
def execute_highest_point(
    body: HighestPointRequest,
    db: Session = Depends(get_db),
) -> ElevationFeature:
    try:
        if body.inputs.polygon:
            polygon = GeoPolygon(coordinates=body.inputs.polygon.coordinates)
        elif body.inputs.zone_id:
            zone = SQLAlchemyZoneRepository(db).find_by_id(body.inputs.zone_id)
            if not zone:
                raise HTTPException(status_code=404, detail="Zone not found")
            polygon = GeoPolygon(coordinates=zone.geometry["coordinates"])
        else:
            raise HTTPException(status_code=422, detail="Must provide either polygon or zone_id")
        point, elevation = get_get_highest_point().execute(polygon)
    except ElevationDataNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return ElevationFeature(
        geometry=PointGeometry(coordinates=[point.longitude, point.latitude]),
        properties={"elevation_m": elevation.meters},
    )


@router.post("/point-elevation/execution", response_model=ElevationFeature)
def execute_point_elevation(
    body: PointElevationRequest,
) -> ElevationFeature:
    try:
        point = GeoPoint(
            longitude=body.inputs.point.coordinates[0],
            latitude=body.inputs.point.coordinates[1],
        )
        elevation = get_get_point_elevation().execute(point)
    except ElevationDataNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return ElevationFeature(
        geometry=PointGeometry(coordinates=[point.longitude, point.latitude]),
        properties={"elevation_m": elevation.meters},
    )
