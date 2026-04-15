"""Query: Get contours for a zone."""

from uuid import UUID

from src.modules.elevation_analysis.domain.entities import ElevationContour
from src.modules.elevation_analysis.domain.ports import ElevationContourRepository


class GetZoneContours:
    """
    Query to retrieve elevation contours stored for a zone.

    Domain-level read operation respecting hexagonal architecture.
    """

    def __init__(self, contour_repo: ElevationContourRepository) -> None:
        self._contour_repo = contour_repo

    def execute(self, zone_id: UUID) -> list[ElevationContour]:
        """
        Execute the query.

        Args:
            zone_id: UUID of the zone

        Returns:
            List of ElevationContour entities, ordered by elevation ascending
        """
        return self._contour_repo.find_by_zone(zone_id)
