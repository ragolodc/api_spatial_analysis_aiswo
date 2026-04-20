"""Command: Run zone elevation analysis and persist characteristic points."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.modules.elevation_analysis.domain.entities import (
    ElevationAnalysis,
    ElevationPoint,
)
from src.modules.elevation_analysis.domain.exceptions import (
    ZoneNotFound,
)
from src.modules.elevation_analysis.domain.ports import (
    ElevationAnalysisProvider,
    ElevationAnalysisRepository,
    ZoneGeometryReader,
)


class RunZoneElevationAnalysis:
    """
    Execute elevation analysis on a stored zone and persist characteristic points
    (highest, lowest, centroid).

    Domain-level command respecting hexagonal architecture.
    """

    def __init__(
        self,
        provider: ElevationAnalysisProvider,
        analysis_repo: ElevationAnalysisRepository,
        zone_reader: ZoneGeometryReader,
    ) -> None:
        self._provider = provider
        self._analysis_repo = analysis_repo
        self._zone_reader = zone_reader

    def execute(
        self,
        zone_id: UUID,
    ) -> ElevationAnalysis:
        """
        Execute the analysis command.

        Args:
            zone_id: UUID of the zone to analyze

        Returns:
            Persisted ElevationAnalysis with characteristic points

        Raises:
            ZoneNotFound: If zone does not exist
            DemNotAvailable: If DEM data not available for zone
        """
        polygon = self._zone_reader.find_polygon(zone_id)
        if not polygon:
            raise ZoneNotFound(f"Zone {zone_id} not found")

        raw_points = self._provider.get_characteristic_points(polygon)

        analysis_id = uuid4()
        points = [
            ElevationPoint(
                id=uuid4(),
                analysis_id=analysis_id,
                point_type=pt,
                longitude=lon,
                latitude=lat,
                elevation_m=elev,
            )
            for pt, lon, lat, elev in raw_points
        ]

        analysis = ElevationAnalysis(
            id=analysis_id,
            zone_id=zone_id,
            source_id=self._provider.source_id,
            analyzed_at=datetime.now(timezone.utc),
            points=points,
        )
        return self._analysis_repo.save(analysis)
