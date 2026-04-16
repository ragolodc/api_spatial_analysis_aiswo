from datetime import datetime, timezone
from uuid import uuid4

import src.modules.zones.presentation.features_router as zones_router
from src.modules.zones.domain.entities import Zone, ZoneType
from src.shared.domain import GeoPolygon


def _sample_zone() -> Zone:
    return Zone(
        id=uuid4(),
        name="North field",
        zone_type=ZoneType.FARM_BOUNDARY,
        geometry=GeoPolygon(coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]),
        created_at=datetime.now(timezone.utc),
    )


def test_list_zones_returns_feature_collection(client, monkeypatch) -> None:
    zone = _sample_zone()

    class _ListZones:
        def execute(self):
            return [zone]

    monkeypatch.setattr(zones_router, "get_list_zones", lambda db: _ListZones())

    response = client.get("/collections/zones/items")

    assert response.status_code == 200
    payload = response.json()
    assert payload["number_matched"] == 1
    assert payload["features"][0]["properties"]["name"] == "North field"


def test_get_zone_returns_404_when_not_found(client, monkeypatch) -> None:
    class _GetZone:
        def execute(self, zone_id):
            return None

    monkeypatch.setattr(zones_router, "get_get_zone", lambda db: _GetZone())

    response = client.get(f"/collections/zones/items/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Zone not found"


def test_create_zone_returns_created_feature(client, monkeypatch) -> None:
    zone = _sample_zone()

    class _CreateZone:
        def execute(self, name, zone_type, geometry):
            assert name == "North field"
            assert zone_type == ZoneType.FARM_BOUNDARY
            assert geometry.coordinates[0][0] == [0.0, 0.0]
            return zone

    monkeypatch.setattr(zones_router, "get_create_zone", lambda db: _CreateZone())

    response = client.post(
        "/collections/zones/items",
        json={
            "name": "North field",
            "zone_type": "farm_boundary",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]],
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["properties"]["zone_type"] == "farm_boundary"
