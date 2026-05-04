from typing import Protocol
from uuid import UUID

from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisAnalytics,
    ProfileAnalysisJob,
    ProfileAnalysisJobRequest,
    ProfileAnalysisResult,
    ProfilePointFilters,
    ProfilePointRow,
    ProfileSamplePoint,
    ProfileSummaryEntry,
    ProfileType,
)


class ProfileAnalysisJobDispatcher(Protocol):
    """Hexagonal outbound port to enqueue async profile-analysis jobs."""

    def dispatch(self, request: ProfileAnalysisJobRequest) -> None: ...


class ProfileAnalysisJobRepository(Protocol):
    """Persistence port for async profile-analysis jobs."""

    def save(self, job: ProfileAnalysisJob) -> ProfileAnalysisJob: ...
    def find_by_id(self, request_id: UUID) -> ProfileAnalysisJob | None: ...
    def update(self, job: ProfileAnalysisJob) -> ProfileAnalysisJob: ...


class ProfileElevationProvider(Protocol):
    """Outbound port for DEM sampling over generated profile points."""

    @property
    def source_id(self) -> UUID: ...

    def sample_points(self, points: list[ProfileSamplePoint]) -> list[ProfileSamplePoint]: ...


class ProfileAnalysisPointWarehouse(Protocol):
    """Analytical storage for flattened profile-analysis point samples."""

    def store_result(self, result: ProfileAnalysisResult) -> None: ...
    def get_analytics(self, request_id: UUID) -> ProfileAnalysisAnalytics | None: ...
    def get_points(
        self,
        request_id: UUID,
        profile_type: ProfileType | None,
        filters: ProfilePointFilters,
        limit: int,
        offset: int,
    ) -> list[ProfilePointRow]: ...
    def get_profile_summaries(self, request_id: UUID) -> list[ProfileSummaryEntry]: ...
