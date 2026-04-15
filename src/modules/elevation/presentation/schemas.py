from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, model_validator


class PolygonGeometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float]


class HighestPointInputs(BaseModel):
    polygon: PolygonGeometry | None = None
    zone_id: UUID | None = None

    @model_validator(mode="after")
    def require_exactly_one_source(self) -> Self:
        if not self.polygon and not self.zone_id:
            raise ValueError("Provide either 'polygon' or 'zone_id'")
        if self.polygon and self.zone_id:
            raise ValueError("Provide either 'polygon' or 'zone_id', not both")
        return self


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


class ElevationSourceItem(BaseModel):
    id: str
    name: str
    srid: int
    source_url: str | None
    collection: str | None
    is_active: bool
    created_at: str


class ElevationSourceCollection(BaseModel):
    items: list[ElevationSourceItem]
