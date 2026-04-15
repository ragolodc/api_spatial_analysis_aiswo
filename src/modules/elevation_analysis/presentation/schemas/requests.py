"""Request schemas for elevation analysis operations."""

from uuid import UUID

from pydantic import BaseModel


class RunAnalysisInputs(BaseModel):
    """Input parameters for zone elevation analysis."""

    zone_id: UUID


class RunAnalysisRequest(BaseModel):
    """Request body for running zone elevation analysis."""

    inputs: RunAnalysisInputs


class GenerateContoursInputs(BaseModel):
    """Input parameters for generating elevation contours."""

    zone_id: UUID
    interval_m: float = 50.0


class GenerateContoursRequest(BaseModel):
    """Request body for generating elevation contours."""

    inputs: GenerateContoursInputs
