from uuid import UUID

from src.modules.profile_analysis.domain.entities import ProfileAnalysisJob
from src.modules.profile_analysis.domain.ports import ProfileAnalysisJobRepository


class GetProfileAnalysisJob:
    """Query use case to retrieve an async profile-analysis job by id."""

    def __init__(self, repository: ProfileAnalysisJobRepository) -> None:
        self._repository = repository

    def execute(self, request_id: UUID) -> ProfileAnalysisJob | None:
        return self._repository.find_by_id(request_id)
