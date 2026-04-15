from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from src.modules.zones.domain.entities import ZoneType


class PolygonGeometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class ZoneProperties(BaseModel):
    id: UUID
    name: str
    zone_type: ZoneType
    created_at: str


class ZoneFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: PolygonGeometry
    properties: ZoneProperties


class ZoneFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[ZoneFeature]
    number_matched: int


class CreateZoneRequest(BaseModel):
    name: str
    zone_type: ZoneType
    geometry: PolygonGeometry
