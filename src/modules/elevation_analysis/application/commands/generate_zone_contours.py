"""Command: Generate and persist contours for a zone."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.modules.elevation_analysis.domain.entities import ElevationContour
from src.modules.elevation_analysis.domain.exceptions import (
    ZoneNotFound,
)
from src.modules.elevation_analysis.domain.ports import (
    ElevationAnalysisProvider,
    ElevationContourRepository,
    ZoneGeometryReader,
)
from src.shared.domain import GeoMultiLineString


class GenerateZoneContours:
    """
    Generate and persist elevation contours for a zone.
    Replaces existing contours if already present.

    Domain-level command respecting hexagonal architecture.
    """

    def __init__(
        self,
        provider: ElevationAnalysisProvider,
        contour_repo: ElevationContourRepository,
        zone_reader: ZoneGeometryReader,
    ) -> None:
        self._provider = provider
        self._contour_repo = contour_repo
        self._zone_reader = zone_reader

    def execute(
        self,
        zone_id: UUID,
        interval_m: float = 50.0,
    ) -> list[ElevationContour]:
        """
        Execute the contour generation command.

        Args:
            zone_id: UUID of the zone
            interval_m: Elevation interval between contours (meters)
            provider_name: Name of the DEM provider

        Returns:
            List of persisted ElevationContour entities

        Raises:
            ZoneNotFound: If zone does not exist
            ContoursGenerationError: If contour generation fails
        """
        polygon = self._zone_reader.find_polygon(zone_id)
        if not polygon:
            raise ZoneNotFound(f"Zone {zone_id} not found")

        raw_contours = self._provider.get_contours(polygon, interval_m)

        now = datetime.now(timezone.utc)
        contours = [
            ElevationContour(
                id=uuid4(),
                zone_id=zone_id,
                provider=self._provider.name,
                interval_m=interval_m,
                elevation_m=elev,
                geometry=GeoMultiLineString(coordinates=geojson["coordinates"]),
                generated_at=now,
            )
            for elev, geojson in raw_contours
        ]

        self._contour_repo.delete_by_zone(zone_id)
        return self._contour_repo.save_all(contours)
