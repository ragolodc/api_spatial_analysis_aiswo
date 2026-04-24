from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class SlopeAnalysisJobAccepted(BaseModel):
    request_id: UUID
    status: Literal["queued"]
    queue: str
