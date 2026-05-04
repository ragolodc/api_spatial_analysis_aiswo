from typing import Any
from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import SlopeAnalysisJobStatus
from src.modules.pivot_geometry_analysis.domain.ports import (
    SlopeAnalysisJobRepository,
    SlopeAnalysisResultReader,
)


class GetSlopeAnalysisResults:
    """Query use case to retrieve slope analysis results for a completed job."""

    def __init__(
        self,
        repository: SlopeAnalysisJobRepository,
        result_reader: SlopeAnalysisResultReader,
    ) -> None:
        self._repository = repository
        self._result_reader = result_reader

    def execute(self, request_id: UUID) -> dict[str, Any] | None:
        """
        Retrieve detailed result payload for a completed job.

        Strategy:
        1. Validate job exists and is completed.
        2. Read normalized full result from analytical storage (ClickHouse).
        3. Return None when analytical storage has no rows for the request.
        """
        job = self._repository.find_by_id(request_id)
        if job is None or job.status != SlopeAnalysisJobStatus.COMPLETED:
            return None

        return self._result_reader.get_result_payload(request_id)
