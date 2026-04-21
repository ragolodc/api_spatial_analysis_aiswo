from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.modules.zones.domain.entities import Zone
from src.modules.zones.infrastructure.factories import get_create_zone, get_get_zone, get_list_zones
from src.modules.zones.presentation.schemas import (
    CreateZoneRequest,
    PolygonGeometry,
    ZoneFeature,
    ZoneFeatureCollection,
    ZoneProperties,
)
from src.shared.domain import GeoPolygon

router = APIRouter(prefix="/collections/zones", tags=["OGC Features - Zones"])


def _to_feature(zone: Zone) -> ZoneFeature:
    return ZoneFeature(
        id=str(zone.id),
        geometry=PolygonGeometry(type="Polygon", coordinates=zone.geometry.coordinates),
        properties=ZoneProperties(
            id=zone.id,
            name=zone.name,
            zone_type=zone.zone_type,
            created_at=zone.created_at.isoformat(),
        ),
    )


@router.get("/items", response_model=ZoneFeatureCollection)
def list_zones(use_case=Depends(get_list_zones)) -> ZoneFeatureCollection:
    zones = use_case.execute()
    features = [_to_feature(z) for z in zones]
    return ZoneFeatureCollection(features=features, number_matched=len(features))


@router.post("/items", response_model=ZoneFeature, status_code=201)
def create_zone(body: CreateZoneRequest, use_case=Depends(get_create_zone)) -> ZoneFeature:
    zone = use_case.execute(
        name=body.name,
        zone_type=body.zone_type,
        geometry=GeoPolygon(coordinates=body.geometry.coordinates),
    )
    return _to_feature(zone)


@router.get("/items/{zone_id}", response_model=ZoneFeature)
def get_zone(zone_id: UUID, use_case=Depends(get_get_zone)) -> ZoneFeature:
    zone = use_case.execute(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return _to_feature(zone)
