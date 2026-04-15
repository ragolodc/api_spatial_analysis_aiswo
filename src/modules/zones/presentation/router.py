from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.modules.zones.application.use_cases import CreateZone, GetZone, ListZones
from src.modules.zones.domain.entities import Zone
from src.modules.zones.infrastructure.persistence.repository import SQLAlchemyZoneRepository
from src.modules.zones.presentation.schemas import (
    CreateZoneRequest,
    PolygonGeometry,
    ZoneFeature,
    ZoneFeatureCollection,
    ZoneProperties,
)
from src.shared.db.session import get_db

router = APIRouter(prefix="/collections/zones", tags=["OGC Features - Zones"])


def _to_feature(zone: Zone) -> ZoneFeature:
    return ZoneFeature(
        id=str(zone.id),
        geometry=PolygonGeometry(**zone.geometry),
        properties=ZoneProperties(
            id=zone.id,
            name=zone.name,
            zone_type=zone.zone_type,
            created_at=zone.created_at.isoformat(),
        ),
    )


@router.get("/items", response_model=ZoneFeatureCollection)
def list_zones(db: Session = Depends(get_db)) -> ZoneFeatureCollection:
    zones = ListZones(SQLAlchemyZoneRepository(db)).execute()
    features = [_to_feature(z) for z in zones]
    return ZoneFeatureCollection(features=features, number_matched=len(features))


@router.post("/items", response_model=ZoneFeature, status_code=201)
def create_zone(body: CreateZoneRequest, db: Session = Depends(get_db)) -> ZoneFeature:
    zone = CreateZone(SQLAlchemyZoneRepository(db)).execute(
        name=body.name,
        zone_type=body.zone_type,
        geometry=body.geometry.model_dump(),
    )
    return _to_feature(zone)


@router.get("/items/{zone_id}", response_model=ZoneFeature)
def get_zone(zone_id: UUID, db: Session = Depends(get_db)) -> ZoneFeature:
    zone = GetZone(SQLAlchemyZoneRepository(db)).execute(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return _to_feature(zone)
