from datetime import datetime, timezone
from uuid import uuid4

from src.modules.zones.application.commands import CreateZone
from src.modules.zones.application.queries import GetZone, ListZones
from src.modules.zones.domain.entities import Zone, ZoneType
from src.shared.domain import GeoPolygon


class FakeZoneRepository:
    def __init__(self, zones: list[Zone] | None = None) -> None:
        self._zones = zones or []
        self.saved_zone: Zone | None = None
        self.last_requested_id = None

    def save(self, zone: Zone) -> Zone:
        self.saved_zone = zone
        self._zones.append(zone)
        return zone

    def find_by_id(self, zone_id):
        self.last_requested_id = zone_id
        for zone in self._zones:
            if zone.id == zone_id:
                return zone
        return None

    def find_all(self):
        return list(self._zones)


def _sample_polygon() -> GeoPolygon:
    return GeoPolygon(coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]])


def test_create_zone_persists_new_zone_with_expected_fields() -> None:
    repo = FakeZoneRepository()
    use_case = CreateZone(repo)

    zone = use_case.execute(
        name="North field",
        zone_type=ZoneType.FARM_BOUNDARY,
        geometry=_sample_polygon(),
    )

    assert repo.saved_zone is not None
    assert zone.name == "North field"
    assert zone.zone_type == ZoneType.FARM_BOUNDARY
    assert zone.geometry.coordinates[0][0] == [0.0, 0.0]
    assert zone.created_at.tzinfo is not None


def test_list_zones_returns_repository_items() -> None:
    zone = Zone(
        id=uuid4(),
        name="Pivot 1",
        zone_type=ZoneType.PIVOT,
        geometry=_sample_polygon(),
        created_at=datetime.now(timezone.utc),
    )
    repo = FakeZoneRepository(zones=[zone])

    result = ListZones(repo).execute()

    assert len(result) == 1
    assert result[0].id == zone.id


def test_get_zone_returns_matching_zone_by_id() -> None:
    zone = Zone(
        id=uuid4(),
        name="Field A",
        zone_type=ZoneType.FARM_BOUNDARY,
        geometry=_sample_polygon(),
        created_at=datetime.now(timezone.utc),
    )
    repo = FakeZoneRepository(zones=[zone])

    result = GetZone(repo).execute(zone.id)

    assert result is not None
    assert repo.last_requested_id == zone.id
    assert result.name == "Field A"
