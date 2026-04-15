"""Command: Run zone elevation analysis and persist characteristic points."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.modules.elevation.domain.value_objects import GeoPolygon
from src.modules.elevation_analysis.domain.entities import (
    ElevationAnalysis,
    ElevationPoint,
)
from src.modules.elevation_analysis.domain.exceptions import (
    DemNotAvailable,
    ZoneNotFound,
)
from src.modules.elevation_analysis.domain.ports import (
    ElevationAnalysisProvider,
    ElevationAnalysisRepository,
)
from src.modules.zones.domain.ports import ZoneRepository


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
        zone_repo: ZoneRepository,
    ) -> None:
        self._provider = provider
        self._analysis_repo = analysis_repo
        self._zone_repo = zone_repo

    def execute(
        self,
        zone_id: UUID,
        provider_name: str = "planetary_computer",
    ) -> ElevationAnalysis:
        """
        Execute the analysis command.

        Args:
            zone_id: UUID of the zone to analyze
            provider_name: Name of the DEM provider

        Returns:
            Persisted ElevationAnalysis with characteristic points

        Raises:
            ZoneNotFound: If zone does not exist
            DemNotAvailable: If DEM data not available for zone
        """
        zone = self._zone_repo.find_by_id(zone_id)
        if not zone:
            raise ZoneNotFound(f"Zone {zone_id} not found")

        try:
            polygon = GeoPolygon(coordinates=zone.geometry["coordinates"])
            raw_points = self._provider.get_characteristic_points(polygon)
        except Exception as exc:
            raise DemNotAvailable(f"DEM not available for zone: {exc}")

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
            provider=provider_name,
            resolution_m=30.0,
            analyzed_at=datetime.now(timezone.utc),
            points=points,
        )
        return self._analysis_repo.save(analysis)
