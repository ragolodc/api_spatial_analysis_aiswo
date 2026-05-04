from typing import Any
from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import SlopeAnalysisResult
from src.modules.pivot_geometry_analysis.domain.ports import SlopeAnalysisJobRepository


class GetSlopeAnalysisResults:
    """Query use case to retrieve slope analysis results for a completed job."""

    def __init__(self, repository: SlopeAnalysisJobRepository) -> None:
        self._repository = repository

    def execute(self, request_id: UUID) -> dict[str, Any] | None:
        """
        Retrieve the result_payload from a completed job.

        Returns None if job not found or if result_payload is None (job not yet completed).
        """
        job = self._repository.find_by_id(request_id)
        if job is None or job.result_payload is None:
            return None
        return job.result_payload
