from uuid import UUID

from src.modules.profile_analysis.domain.entities import ProfilePointRow, ProfileType
from src.modules.profile_analysis.domain.ports import ProfileAnalysisPointWarehouse


class GetProfileAnalysisPoints:
    """Query handler to retrieve paginated profile sample points from the warehouse."""

    def __init__(self, warehouse: ProfileAnalysisPointWarehouse) -> None:
        self._warehouse = warehouse

    def execute(
        self,
        request_id: UUID,
        profile_type: ProfileType | None,
        limit: int,
        offset: int,
    ) -> list[ProfilePointRow]:
        return self._warehouse.get_points(
            request_id=request_id,
            profile_type=profile_type,
            limit=limit,
            offset=offset,
        )
