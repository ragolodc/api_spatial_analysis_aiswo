from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import SlopeAnalysisJob
from src.modules.pivot_geometry_analysis.domain.ports import SlopeAnalysisJobRepository


class GetSlopeAnalysisJob:
    """Query use case to retrieve an async slope-analysis job by id."""

    def __init__(self, repository: SlopeAnalysisJobRepository) -> None:
        self._repository = repository

    def execute(self, request_id: UUID) -> SlopeAnalysisJob | None:
        return self._repository.find_by_id(request_id)
