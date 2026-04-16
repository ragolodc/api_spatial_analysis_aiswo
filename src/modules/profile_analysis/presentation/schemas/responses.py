from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ProfileAnalysisJobAccepted(BaseModel):
    request_id: UUID
    status: Literal["queued"]
    queue: str


class ProfileAnalysisJobResponse(BaseModel):
    request_id: UUID
    zone_id: UUID
    status: Literal["queued", "running", "completed", "failed"]
    error_message: str | None
    queued_at: str
    started_at: str | None
    completed_at: str | None
    result_payload: dict | None


class ProfileAnalysisAnalyticsResponse(BaseModel):
    request_id: UUID
    total_points: int
    min_elevation_m: float | None
    max_elevation_m: float | None
    avg_elevation_m: float | None
