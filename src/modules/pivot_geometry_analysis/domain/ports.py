from typing import Any, Protocol
from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJob,
    SlopeAnalysisJobRequest,
)
from src.modules.profile_analysis.domain.entities import (
    LongitudinalProfile,
    SpansConfig,
    TransverseProfile,
)


class ProfileReader(Protocol):
    """Read already-sampled profiles produced by the profile_analysis module."""

    def get_longitudinal_profiles(self, request_id: UUID) -> list[LongitudinalProfile]:
        """Return all sampled longitudinal profiles for *request_id*."""
        ...

    def get_transversal_profiles(self, request_id: UUID) -> list[TransverseProfile]:
        """Return all sampled transversal profiles for *request_id*."""
        ...

    def get_spans_configurations(self, request_id: UUID) -> SpansConfig:
        """Return the span configurations."""
        ...


class SlopeAnalysisJobRepository(Protocol):
    """Persistence port for async slope-analysis jobs."""

    def save(self, job: SlopeAnalysisJob) -> SlopeAnalysisJob: ...
    def find_by_id(self, request_id: UUID) -> SlopeAnalysisJob | None: ...
    def update(self, job: SlopeAnalysisJob) -> SlopeAnalysisJob: ...


class SlopeAnalysisJobDispatcher(Protocol):
    """Hexagonal outbound port to enqueue async slope-analysis jobs."""

    def dispatch(self, request: SlopeAnalysisJobRequest) -> None: ...


class SlopeAnalysisResultReader(Protocol):
    """Read normalized slope-analysis results from analytical storage."""

    def get_result_payload(self, request_id: UUID) -> dict[str, Any] | None: ...


class SlopeAnalysisResultWriter(Protocol):
    """Persist normalized slope-analysis results into analytical storage."""

    def store_result(self, analysis, job_request: SlopeAnalysisJobRequest) -> None: ...
