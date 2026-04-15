from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class PolygonGeometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float]


class HighestPointInputs(BaseModel):
    polygon: Optional[PolygonGeometry] = None
    zone_id: Optional[UUID] = None


class HighestPointRequest(BaseModel):
    inputs: HighestPointInputs


class PointElevationInputs(BaseModel):
    point: PointGeometry


class PointElevationRequest(BaseModel):
    inputs: PointElevationInputs


class ElevationFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: dict
