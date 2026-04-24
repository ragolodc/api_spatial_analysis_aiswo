from typing import Protocol
from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJob,
    SlopeAnalysisJobRequest,
)
from src.modules.profile_analysis.domain.entities import LongitudinalProfile, TransverseProfile


class ProfileReader(Protocol):
    """Read already-sampled profiles produced by the profile_analysis module."""

    def get_longitudinal_profiles(self, request_id: UUID) -> list[LongitudinalProfile]:
        """Return all sampled longitudinal profiles for *request_id*."""
        ...

    def get_transversal_profiles(self, request_id: UUID) -> list[TransverseProfile]:
        """Return all sampled transversal profiles for *request_id*."""
        ...

    def get_radii_m(self, request_id: UUID) -> tuple[float, ...]:
        """Return the ordered tower radii (metres) from the original job payload."""
        ...


class SlopeAnalysisJobRepository(Protocol):
    """Persistence port for async slope-analysis jobs."""

    def save(self, job: SlopeAnalysisJob) -> SlopeAnalysisJob: ...
    def find_by_id(self, request_id: UUID) -> SlopeAnalysisJob | None: ...
    def update(self, job: SlopeAnalysisJob) -> SlopeAnalysisJob: ...


class SlopeAnalysisJobDispatcher(Protocol):
    """Hexagonal outbound port to enqueue async slope-analysis jobs."""

    def dispatch(self, request: SlopeAnalysisJobRequest) -> None: ...
