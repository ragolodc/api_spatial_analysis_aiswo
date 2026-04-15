"""GeoJSON geometry schemas for elevation analysis."""

from typing import Literal

from pydantic import BaseModel


class PointGeometry(BaseModel):
    """GeoJSON Point geometry."""

    type: Literal["Point"] = "Point"
    coordinates: list[float]


class MultiLineStringGeometry(BaseModel):
    """GeoJSON MultiLineString geometry for elevation contours."""

    type: Literal["MultiLineString"] = "MultiLineString"
    coordinates: list[list[list[float]]]
