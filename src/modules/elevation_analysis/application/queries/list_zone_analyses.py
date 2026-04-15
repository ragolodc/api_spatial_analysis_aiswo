"""Query: List all analyses for a zone."""

from uuid import UUID

from src.modules.elevation_analysis.domain.entities import ElevationAnalysis
from src.modules.elevation_analysis.domain.ports import ElevationAnalysisRepository


class ListZoneAnalyses:
    """
    Query to retrieve all elevation analyses executed on a zone.

    Domain-level read operation respecting hexagonal architecture.
    """

    def __init__(self, analysis_repo: ElevationAnalysisRepository) -> None:
        self._analysis_repo = analysis_repo

    def execute(self, zone_id: UUID) -> list[ElevationAnalysis]:
        """
        Execute the query.

        Args:
            zone_id: UUID of the zone

        Returns:
            List of ElevationAnalysis entities, ordered by most recent first
        """
        return self._analysis_repo.find_by_zone(zone_id)
