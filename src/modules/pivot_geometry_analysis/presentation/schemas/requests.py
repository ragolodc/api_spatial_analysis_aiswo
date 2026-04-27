from uuid import UUID

from pydantic import BaseModel


class SlopeAnalysisInputs(BaseModel):
    zone_id: UUID
    profile_analysis_id: UUID


class QueueSlopeAnalysisRequest(BaseModel):
    inputs: SlopeAnalysisInputs
