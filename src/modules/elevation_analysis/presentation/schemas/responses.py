"""Response schemas for elevation analysis OGC API Features."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from src.modules.elevation_analysis.domain.entities import PointType
from src.modules.elevation_analysis.presentation.schemas.geometries import (
    MultiLineStringGeometry,
    PointGeometry,
)

# --- OGC Feature response schemas ---


class ElevationPointProperties(BaseModel):
    """Properties of a characteristic elevation point."""

    point_type: PointType
    elevation_m: float
    analysis_id: UUID


class ElevationPointFeature(BaseModel):
    """GeoJSON Feature for a characteristic elevation point."""

    type: Literal["Feature"] = "Feature"
    id: str
    geometry: PointGeometry
    properties: ElevationPointProperties


class AnalysisProperties(BaseModel):
    """Properties of an elevation analysis."""

    zone_id: UUID
    source_id: UUID
    analyzed_at: str


class ElevationAnalysisFeature(BaseModel):
    """GeoJSON Feature representing an elevation analysis with characteristic points."""

    type: Literal["Feature"] = "Feature"
    id: str
    geometry: Literal[None] = None
    properties: AnalysisProperties
    characteristic_points: list[ElevationPointFeature]


class ElevationAnalysisCollection(BaseModel):
    """GeoJSON FeatureCollection of elevation analyses."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[ElevationAnalysisFeature]
    number_matched: int


class ContourProperties(BaseModel):
    """Properties of an elevation contour."""

    zone_id: UUID
    elevation_m: float
    interval_m: float
    source_id: UUID
    generated_at: str


class ElevationContourFeature(BaseModel):
    """GeoJSON Feature representing an elevation contour line."""

    type: Literal["Feature"] = "Feature"
    id: str
    geometry: MultiLineStringGeometry
    properties: ContourProperties


class ElevationContourCollection(BaseModel):
    """GeoJSON FeatureCollection of elevation contours."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[ElevationContourFeature]
    number_matched: int
