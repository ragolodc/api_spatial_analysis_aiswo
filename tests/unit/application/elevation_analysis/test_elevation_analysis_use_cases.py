from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.modules.elevation_analysis.application.commands import (
    GenerateZoneContours,
    RunZoneElevationAnalysis,
)
from src.modules.elevation_analysis.application.queries import GetZoneContours, ListZoneAnalyses
from src.modules.elevation_analysis.domain.entities import (
    ElevationAnalysis,
    ElevationContour,
    PointType,
)
from src.modules.elevation_analysis.domain.exceptions import ZoneNotFound
from src.shared.domain import GeoMultiLineString, GeoPolygon


class FakeZoneReader:
    def __init__(self, polygon: GeoPolygon | None) -> None:
        self._polygon = polygon

    def find_polygon(self, zone_id):
        return self._polygon


class FakeAnalysisProvider:
    @property
    def name(self) -> str:
        return "planetary_computer"

    @property
    def resolution_m(self) -> float:
        return 30.0

    def get_characteristic_points(self, polygon: GeoPolygon):
        return [
            (PointType.HIGHEST, -74.1, 4.6, 2567.3),
            (PointType.LOWEST, -74.0, 4.5, 2475.0),
            (PointType.CENTROID, -74.05, 4.55, 2520.2),
        ]

    def get_contours(self, polygon: GeoPolygon, interval_m: float):
        return [
            (
                2500.0,
                {
                    "type": "MultiLineString",
                    "coordinates": [[[-74.2, 4.5], [-74.1, 4.55], [-74.0, 4.6]]],
                },
            )
        ]


class FakeAnalysisRepository:
    def __init__(self) -> None:
        self.saved_analysis: ElevationAnalysis | None = None
        self.items: list[ElevationAnalysis] = []

    def save(self, analysis: ElevationAnalysis):
        self.saved_analysis = analysis
        self.items.append(analysis)
        return analysis

    def find_by_id(self, analysis_id):
        return next((a for a in self.items if a.id == analysis_id), None)

    def find_by_zone(self, zone_id):
        return [a for a in self.items if a.zone_id == zone_id]


class FakeContourRepository:
    def __init__(self) -> None:
        self.deleted_zone_id = None
        self.saved_contours: list[ElevationContour] = []

    def delete_by_zone(self, zone_id):
        self.deleted_zone_id = zone_id

    def save_all(self, contours: list[ElevationContour]):
        self.saved_contours = list(contours)
        return contours

    def find_by_zone(self, zone_id):
        return [c for c in self.saved_contours if c.zone_id == zone_id]


def _sample_polygon() -> GeoPolygon:
    return GeoPolygon(
        coordinates=[[[-74.2, 4.5], [-74.0, 4.5], [-74.0, 4.7], [-74.2, 4.5]]]
    )


def test_run_zone_elevation_analysis_raises_when_zone_missing() -> None:
    use_case = RunZoneElevationAnalysis(
        provider=FakeAnalysisProvider(),
        analysis_repo=FakeAnalysisRepository(),
        zone_reader=FakeZoneReader(polygon=None),
    )

    with pytest.raises(ZoneNotFound):
        use_case.execute(zone_id=uuid4())


def test_run_zone_elevation_analysis_saves_analysis_with_points() -> None:
    zone_id = uuid4()
    repo = FakeAnalysisRepository()
    use_case = RunZoneElevationAnalysis(
        provider=FakeAnalysisProvider(),
        analysis_repo=repo,
        zone_reader=FakeZoneReader(polygon=_sample_polygon()),
    )

    analysis = use_case.execute(zone_id=zone_id)

    assert repo.saved_analysis is not None
    assert analysis.zone_id == zone_id
    assert analysis.provider == "planetary_computer"
    assert analysis.resolution_m == 30.0
    assert len(analysis.points) == 3
    assert {p.point_type for p in analysis.points} == {
        PointType.HIGHEST,
        PointType.LOWEST,
        PointType.CENTROID,
    }


def test_generate_zone_contours_raises_when_zone_missing() -> None:
    use_case = GenerateZoneContours(
        provider=FakeAnalysisProvider(),
        contour_repo=FakeContourRepository(),
        zone_reader=FakeZoneReader(polygon=None),
    )

    with pytest.raises(ZoneNotFound):
        use_case.execute(zone_id=uuid4(), interval_m=50.0)


def test_generate_zone_contours_replaces_and_saves_contours() -> None:
    zone_id = uuid4()
    contour_repo = FakeContourRepository()
    use_case = GenerateZoneContours(
        provider=FakeAnalysisProvider(),
        contour_repo=contour_repo,
        zone_reader=FakeZoneReader(polygon=_sample_polygon()),
    )

    contours = use_case.execute(zone_id=zone_id, interval_m=25.0)

    assert contour_repo.deleted_zone_id == zone_id
    assert len(contours) == 1
    contour = contours[0]
    assert contour.provider == "planetary_computer"
    assert contour.interval_m == 25.0
    assert contour.elevation_m == 2500.0
    assert isinstance(contour.geometry, GeoMultiLineString)
    assert contour.geometry.coordinates[0][0] == [-74.2, 4.5]


def test_list_zone_analyses_delegates_repository_query() -> None:
    zone_id = uuid4()
    repo = FakeAnalysisRepository()
    repo.items.append(
        ElevationAnalysis(
            id=uuid4(),
            zone_id=zone_id,
            provider="planetary_computer",
            resolution_m=30.0,
            analyzed_at=datetime.now(timezone.utc),
            points=[],
        )
    )

    result = ListZoneAnalyses(repo).execute(zone_id)

    assert len(result) == 1
    assert result[0].zone_id == zone_id


def test_get_zone_contours_delegates_repository_query() -> None:
    zone_id = uuid4()
    repo = FakeContourRepository()
    repo.saved_contours.append(
        ElevationContour(
            id=uuid4(),
            zone_id=zone_id,
            provider="planetary_computer",
            interval_m=50.0,
            elevation_m=2500.0,
            geometry=GeoMultiLineString(coordinates=[[[-74.2, 4.5], [-74.1, 4.55]]]),
            generated_at=datetime.now(timezone.utc),
        )
    )

    result = GetZoneContours(repo).execute(zone_id)

    assert len(result) == 1
    assert result[0].zone_id == zone_id
