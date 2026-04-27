from datetime import datetime, timezone
from uuid import uuid4

from src.main import app
from src.modules.elevation_analysis.domain.entities import (
    ElevationAnalysis,
    ElevationContour,
    ElevationPoint,
    PointType,
)
from src.modules.elevation_analysis.domain.exceptions import ZoneNotFound
from src.modules.elevation_analysis.infrastructure.factories import (
    get_generate_zone_contours,
    get_get_zone_contours,
    get_list_zone_analyses,
    get_run_zone_elevation_analysis,
)
from src.shared.domain import GeoMultiLineString
from src.shared.domain.exceptions import DemNotAvailable

_API_V1_PREFIX = "/api/v1"


def _sample_analysis() -> ElevationAnalysis:
    analysis_id = uuid4()
    source_id = uuid4()
    point = ElevationPoint(
        id=uuid4(),
        analysis_id=analysis_id,
        point_type=PointType.HIGHEST,
        longitude=-74.1,
        latitude=4.6,
        elevation_m=2567.3,
    )
    return ElevationAnalysis(
        id=analysis_id,
        zone_id=uuid4(),
        source_id=source_id,
        analyzed_at=datetime.now(timezone.utc),
        points=[point],
    )


def _sample_contour(zone_id) -> ElevationContour:
    return ElevationContour(
        id=uuid4(),
        zone_id=zone_id,
        source_id=uuid4(),
        interval_m=50.0,
        elevation_m=2500.0,
        geometry=GeoMultiLineString(coordinates=[[[-74.2, 4.5], [-74.1, 4.55], [-74.0, 4.6]]]),
        generated_at=datetime.now(timezone.utc),
    )


def test_run_zone_elevation_analysis_returns_feature(client) -> None:
    analysis = _sample_analysis()

    class _RunAnalysis:
        def execute(self, zone_id):
            assert zone_id == analysis.zone_id
            return analysis

    app.dependency_overrides[get_run_zone_elevation_analysis] = lambda: _RunAnalysis()

    response = client.post(
        _API_V1_PREFIX + "/processes/analyze-zone-elevation/execution",
        json={"inputs": {"zone_id": str(analysis.zone_id)}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["properties"]["source_id"] == str(analysis.source_id)
    assert len(payload["characteristic_points"]) == 1


def test_run_zone_elevation_analysis_maps_zone_not_found(client) -> None:
    class _RunAnalysis:
        def execute(self, zone_id):
            raise ZoneNotFound("Zone does not exist")

    app.dependency_overrides[get_run_zone_elevation_analysis] = lambda: _RunAnalysis()

    response = client.post(
        _API_V1_PREFIX + "/processes/analyze-zone-elevation/execution",
        json={"inputs": {"zone_id": str(uuid4())}},
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Zone does not exist"


def test_generate_zone_contours_maps_dem_not_available(client) -> None:
    class _GenerateContours:
        def execute(self, zone_id, interval_m):
            raise DemNotAvailable("DEM source unavailable")

    app.dependency_overrides[get_generate_zone_contours] = lambda: _GenerateContours()

    response = client.post(
        _API_V1_PREFIX + "/processes/generate-zone-contours/execution",
        json={"inputs": {"zone_id": str(uuid4()), "interval_m": 100.0}},
    )

    assert response.status_code == 503
    assert response.json()["message"] == "DEM source unavailable"


def test_get_zone_contours_returns_feature_collection(client) -> None:
    zone_id = uuid4()
    contour = _sample_contour(zone_id)

    class _GetContours:
        def execute(self, requested_zone_id):
            assert requested_zone_id == zone_id
            return [contour]

    app.dependency_overrides[get_get_zone_contours] = lambda: _GetContours()

    response = client.get(f"{_API_V1_PREFIX}/collections/zone-contours/items?zone_id={zone_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["number_matched"] == 1
    assert payload["features"][0]["geometry"]["type"] == "MultiLineString"


def test_list_zone_analyses_returns_feature_collection(client) -> None:
    analysis = _sample_analysis()

    class _ListAnalyses:
        def execute(self, zone_id):
            assert zone_id == analysis.zone_id
            return [analysis]

    app.dependency_overrides[get_list_zone_analyses] = lambda: _ListAnalyses()

    response = client.get(
        f"{_API_V1_PREFIX}/collections/zone-analyses/items?zone_id={analysis.zone_id}"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["number_matched"] == 1
    assert payload["features"][0]["properties"]["zone_id"] == str(analysis.zone_id)
