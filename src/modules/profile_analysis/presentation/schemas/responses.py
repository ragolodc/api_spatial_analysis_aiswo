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


class ProfilePointRowResponse(BaseModel):
    profile_type: str
    profile_key: str
    point_index: int
    radius_m: float
    angle_deg: float
    distance_m: float
    longitude: float
    latitude: float
    elevation_m: float | None


class ProfilePointsResponse(BaseModel):
    request_id: UUID
    total: int
    limit: int
    offset: int
    items: list[ProfilePointRowResponse]


class ProfileSummaryEntryResponse(BaseModel):
    profile_type: str
    profile_key: str
    total_points: int
    min_elevation_m: float | None
    max_elevation_m: float | None
    avg_elevation_m: float | None


class ProfileSummaryResponse(BaseModel):
    request_id: UUID
    profiles: list[ProfileSummaryEntryResponse]
