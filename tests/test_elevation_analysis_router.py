from datetime import datetime, timezone
from uuid import uuid4

import src.modules.elevation_analysis.presentation.features_router as analysis_features_router
import src.modules.elevation_analysis.presentation.processes_router as analysis_processes_router
from src.modules.elevation_analysis.domain.entities import (
    ElevationAnalysis,
    ElevationContour,
    ElevationPoint,
    PointType,
)
from src.modules.elevation_analysis.domain.exceptions import DemNotAvailable, ZoneNotFound
from src.shared.domain import GeoMultiLineString

_API_V1_PREFIX = "/api/v1"


def _sample_analysis() -> ElevationAnalysis:
    analysis_id = uuid4()
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
        provider="planetary_computer",
        resolution_m=30.0,
        analyzed_at=datetime.now(timezone.utc),
        points=[point],
    )


def _sample_contour(zone_id) -> ElevationContour:
    return ElevationContour(
        id=uuid4(),
        zone_id=zone_id,
        provider="planetary_computer",
        interval_m=50.0,
        elevation_m=2500.0,
        geometry=GeoMultiLineString(coordinates=[[[-74.2, 4.5], [-74.1, 4.55], [-74.0, 4.6]]]),
        generated_at=datetime.now(timezone.utc),
    )


def test_run_zone_elevation_analysis_returns_feature(client, monkeypatch) -> None:
    analysis = _sample_analysis()

    class _RunAnalysis:
        def execute(self, zone_id):
            assert zone_id == analysis.zone_id
            return analysis

    monkeypatch.setattr(
        analysis_processes_router,
        "get_run_zone_elevation_analysis",
        lambda db: _RunAnalysis(),
    )

    response = client.post(
        _API_V1_PREFIX + "/processes/analyze-zone-elevation/execution",
        json={"inputs": {"zone_id": str(analysis.zone_id)}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["properties"]["provider"] == "planetary_computer"
    assert len(payload["characteristic_points"]) == 1


def test_run_zone_elevation_analysis_maps_zone_not_found(client, monkeypatch) -> None:
    class _RunAnalysis:
        def execute(self, zone_id):
            raise ZoneNotFound("Zone does not exist")

    monkeypatch.setattr(
        analysis_processes_router,
        "get_run_zone_elevation_analysis",
        lambda db: _RunAnalysis(),
    )

    response = client.post(
        _API_V1_PREFIX + "/processes/analyze-zone-elevation/execution",
        json={"inputs": {"zone_id": str(uuid4())}},
    )
    print("----------------------------------------------")

    assert response.status_code == 404
    assert response.json()["message"] == "Zone does not exist"


def test_generate_zone_contours_maps_dem_not_available(client, monkeypatch) -> None:
    class _GenerateContours:
        def execute(self, zone_id, interval_m):
            raise DemNotAvailable("DEM source unavailable")

    monkeypatch.setattr(
        analysis_processes_router,
        "get_generate_zone_contours",
        lambda db: _GenerateContours(),
    )

    response = client.post(
        _API_V1_PREFIX + "/processes/generate-zone-contours/execution",
        json={"inputs": {"zone_id": str(uuid4()), "interval_m": 100.0}},
    )

    assert response.status_code == 503
    assert response.json()["message"] == "DEM source unavailable"


def test_get_zone_contours_returns_feature_collection(client, monkeypatch) -> None:
    zone_id = uuid4()
    contour = _sample_contour(zone_id)

    class _GetContours:
        def execute(self, requested_zone_id):
            assert requested_zone_id == zone_id
            return [contour]

    monkeypatch.setattr(
        analysis_features_router, "get_get_zone_contours", lambda db: _GetContours()
    )

    response = client.get(f"{_API_V1_PREFIX}/collections/zone-contours/items?zone_id={zone_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["number_matched"] == 1
    assert payload["features"][0]["geometry"]["type"] == "MultiLineString"


def test_list_zone_analyses_returns_feature_collection(client, monkeypatch) -> None:
    analysis = _sample_analysis()

    class _ListAnalyses:
        def execute(self, zone_id):
            assert zone_id == analysis.zone_id
            return [analysis]

    monkeypatch.setattr(
        analysis_features_router, "get_list_zone_analyses", lambda db: _ListAnalyses()
    )

    response = client.get(
        f"{_API_V1_PREFIX}/collections/zone-analyses/items?zone_id={analysis.zone_id}"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["number_matched"] == 1
    assert payload["features"][0]["properties"]["zone_id"] == str(analysis.zone_id)
