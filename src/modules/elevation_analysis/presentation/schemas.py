from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from src.modules.elevation_analysis.domain.entities import PointType


# --- Input schemas ---

class RunAnalysisInputs(BaseModel):
    zone_id: UUID


class RunAnalysisRequest(BaseModel):
    inputs: RunAnalysisInputs


class GenerateContoursInputs(BaseModel):
    zone_id: UUID
    interval_m: float = 50.0


class GenerateContoursRequest(BaseModel):
    inputs: GenerateContoursInputs


# --- GeoJSON geometry schemas ---

class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float]


class MultiLineStringGeometry(BaseModel):
    type: Literal["MultiLineString"] = "MultiLineString"
    coordinates: list[list[list[float]]]


# --- OGC Feature response schemas ---

class ElevationPointProperties(BaseModel):
    point_type: PointType
    elevation_m: float
    analysis_id: UUID


class ElevationPointFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: PointGeometry
    properties: ElevationPointProperties


class AnalysisProperties(BaseModel):
    zone_id: UUID
    provider: str
    resolution_m: float
    analyzed_at: str


class ElevationAnalysisFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: Literal[None] = None
    properties: AnalysisProperties
    characteristic_points: list[ElevationPointFeature]


class ElevationAnalysisCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[ElevationAnalysisFeature]
    number_matched: int


class ContourProperties(BaseModel):
    zone_id: UUID
    elevation_m: float
    interval_m: float
    provider: str
    generated_at: str


class ElevationContourFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: MultiLineStringGeometry
    properties: ContourProperties


class ElevationContourCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[ElevationContourFeature]
    number_matched: int
