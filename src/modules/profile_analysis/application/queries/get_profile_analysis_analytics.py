from uuid import UUID

from src.modules.profile_analysis.domain.entities import ProfileAnalysisAnalytics
from src.modules.profile_analysis.domain.ports import ProfileAnalysisPointWarehouse


class GetProfileAnalysisAnalytics:
    """Query use case to retrieve aggregated analytics for a profile-analysis job."""

    def __init__(self, warehouse: ProfileAnalysisPointWarehouse) -> None:
        self._warehouse = warehouse

    def execute(self, request_id: UUID) -> ProfileAnalysisAnalytics | None:
        return self._warehouse.get_analytics(request_id)
