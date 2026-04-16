from uuid import UUID

from src.modules.profile_analysis.domain.entities import ProfileSummaryEntry
from src.modules.profile_analysis.domain.ports import ProfileAnalysisPointWarehouse


class GetProfileAnalysisSummary:
    """Query handler to retrieve per-profile aggregated elevation statistics."""

    def __init__(self, warehouse: ProfileAnalysisPointWarehouse) -> None:
        self._warehouse = warehouse

    def execute(self, request_id: UUID) -> list[ProfileSummaryEntry]:
        return self._warehouse.get_profile_summaries(request_id=request_id)
