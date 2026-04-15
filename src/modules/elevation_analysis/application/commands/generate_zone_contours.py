"""Command: Generate and persist contours for a zone."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.modules.elevation.domain.value_objects import GeoPolygon
from src.modules.elevation_analysis.domain.entities import ElevationContour
from src.modules.elevation_analysis.domain.exceptions import (
    ContoursGenerationError,
    ZoneNotFound,
)
from src.modules.elevation_analysis.domain.ports import (
    ElevationAnalysisProvider,
    ElevationContourRepository,
)
from src.modules.zones.domain.ports import ZoneRepository


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
        zone_repo: ZoneRepository,
    ) -> None:
        self._provider = provider
        self._contour_repo = contour_repo
        self._zone_repo = zone_repo

    def execute(
        self,
        zone_id: UUID,
        interval_m: float = 50.0,
        provider_name: str = "planetary_computer",
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
        zone = self._zone_repo.find_by_id(zone_id)
        if not zone:
            raise ZoneNotFound(f"Zone {zone_id} not found")

        try:
            polygon = GeoPolygon(coordinates=zone.geometry["coordinates"])
            raw_contours = self._provider.get_contours(polygon, interval_m)
        except Exception as exc:
            raise ContoursGenerationError(f"Failed to generate contours: {exc}")

        now = datetime.now(timezone.utc)
        contours = [
            ElevationContour(
                id=uuid4(),
                zone_id=zone_id,
                provider=provider_name,
                interval_m=interval_m,
                elevation_m=elev,
                geometry=geojson,
                generated_at=now,
            )
            for elev, geojson in raw_contours
        ]

        self._contour_repo.delete_by_zone(zone_id)
        return self._contour_repo.save_all(contours)
