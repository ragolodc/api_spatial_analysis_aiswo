from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.shared.domain.entities import Spans


class ProfileAnalysisInputs(BaseModel):
    zone_id: UUID
    pivot_kind: Literal["circular", "sectorial"]
    center: list[float] = Field(min_length=2, max_length=2)
    spans: list[Spans] = Field(min_length=1)
    transverse_spacing_m: float = Field(default=5.0, gt=0)
    longitudinal_spacing_m: float = Field(default=5.0, gt=0)
    angular_spacing_deg: float = Field(default=10.0, gt=0, le=180)
    start_angle_deg: float | None = None
    end_angle_deg: float | None = None
    estimated_points: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_sectorial_fields(self) -> Self:
        if self.pivot_kind == "sectorial":
            if self.start_angle_deg is None or self.end_angle_deg is None:
                raise ValueError("sectorial pivots require start_angle_deg and end_angle_deg")
        return self


class QueueProfileAnalysisRequest(BaseModel):
    inputs: ProfileAnalysisInputs


class ProfileAnalysisPointFiltersQuery(BaseModel):
    profile_key: str | None = None
    min_distance_m: float | None = Field(default=None, ge=0)
    max_distance_m: float | None = Field(default=None, ge=0)
    min_elevation_m: float | None = None
    max_elevation_m: float | None = None

    @model_validator(mode="after")
    def validate_ranges(self) -> Self:
        if (
            self.min_distance_m is not None
            and self.max_distance_m is not None
            and self.min_distance_m > self.max_distance_m
        ):
            raise ValueError("min_distance_m cannot be greater than max_distance_m")
        if (
            self.min_elevation_m is not None
            and self.max_elevation_m is not None
            and self.min_elevation_m > self.max_elevation_m
        ):
            raise ValueError("min_elevation_m cannot be greater than max_elevation_m")
        return self
