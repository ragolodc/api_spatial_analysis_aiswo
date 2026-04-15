from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.modules.elevation.domain.value_objects import GeoPolygon
from src.modules.elevation_analysis.domain.entities import (
    ElevationAnalysis,
    ElevationContour,
    ElevationPoint,
)
from src.modules.elevation_analysis.domain.ports import (
    ElevationAnalysisProvider,
    ElevationAnalysisRepository,
    ElevationContourRepository,
)
from src.modules.zones.domain.ports import ZoneRepository


class RunZoneElevationAnalysis:
    """
    Ejecuta un análisis de elevación sobre una zona almacenada y persiste los
    puntos característicos (más alto, más bajo, centroide).
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
        zone = self._zone_repo.find_by_id(zone_id)
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")

        polygon = GeoPolygon(coordinates=zone.geometry["coordinates"])
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
            provider=provider_name,
            resolution_m=30.0,
            analyzed_at=datetime.now(timezone.utc),
            points=points,
        )
        return self._analysis_repo.save(analysis)


class GenerateZoneContours:
    """
    Genera y persiste las curvas de nivel de una zona a partir del DEM.
    Reemplaza las curvas existentes de la zona si ya hubiera.
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
        zone = self._zone_repo.find_by_id(zone_id)
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")

        polygon = GeoPolygon(coordinates=zone.geometry["coordinates"])
        raw_contours = self._provider.get_contours(polygon, interval_m)

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


class GetZoneAnalyses:
    """Lista todos los análisis de elevación ejecutados sobre una zona."""

    def __init__(self, analysis_repo: ElevationAnalysisRepository) -> None:
        self._analysis_repo = analysis_repo

    def execute(self, zone_id: UUID) -> list[ElevationAnalysis]:
        return self._analysis_repo.find_by_zone(zone_id)


class GetZoneContours:
    """Devuelve las curvas de nivel almacenadas para una zona."""

    def __init__(self, contour_repo: ElevationContourRepository) -> None:
        self._contour_repo = contour_repo

    def execute(self, zone_id: UUID) -> list[ElevationContour]:
        return self._contour_repo.find_by_zone(zone_id)
