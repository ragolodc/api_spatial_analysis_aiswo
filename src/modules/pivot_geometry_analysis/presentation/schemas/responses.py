from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class SlopeAnalysisJobAccepted(BaseModel):
    request_id: UUID
    status: Literal["queued"]
    queue: str


class SlopeAnalysisJobResponse(BaseModel):
    """Response model for GET /processes/slope-analysis/jobs/{request_id}"""

    request_id: UUID
    zone_id: UUID
    status: str
    error_message: str | None
    queued_at: str
    started_at: str | None
    completed_at: str | None
    result_payload: dict[str, Any] | None


class SlopeAnalysisResultsResponse(BaseModel):
    """Response model for GET /processes/slope-analysis/jobs/{request_id}/results"""

    request_id: UUID
    result_payload: dict[str, Any]
