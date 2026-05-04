from uuid import uuid4

from src.modules.profile_analysis.domain.entities import ProfilePointFilters, ProfileType
from src.modules.profile_analysis.infrastructure.warehouses import (
    ClickHouseProfilePointWarehouse,
)


class _QueryResult:
    def __init__(self, result_rows):
        self.result_rows = result_rows


class _FakeClickHouseClient:
    def __init__(self, result_rows):
        self._result_rows = result_rows
        self.query_calls = []

    def query(self, query, parameters):
        self.query_calls.append({"query": query, "parameters": parameters})
        return _QueryResult(self._result_rows)


def test_get_points_builds_query_with_optional_filters() -> None:
    request_id = uuid4()
    client = _FakeClickHouseClient(
        [
            (
                "transverse",
                "radius:100.0",
                0,
                100.0,
                0.0,
                100.0,
                -74.05,
                4.61,
                120.5,
            )
        ]
    )
    warehouse = ClickHouseProfilePointWarehouse(client=client, database="analytics")

    rows = warehouse.get_points(
        request_id=request_id,
        profile_type=ProfileType.TRANSVERSE,
        filters=ProfilePointFilters(
            profile_key="radius:100.0",
            min_distance_m=50.0,
            max_distance_m=150.0,
            min_elevation_m=110.0,
            max_elevation_m=130.0,
        ),
        limit=25,
        offset=5,
    )

    assert len(rows) == 1
    assert rows[0].profile_type == ProfileType.TRANSVERSE
    assert len(client.query_calls) == 1

    executed_query = client.query_calls[0]["query"]
    executed_params = client.query_calls[0]["parameters"]

    assert "WHERE request_id = %(request_id)s" in executed_query
    assert "profile_type = %(profile_type)s" in executed_query
    assert "profile_key = %(profile_key)s" in executed_query
    assert "distance_m >= %(min_distance_m)s" in executed_query
    assert "distance_m <= %(max_distance_m)s" in executed_query
    assert "elevation_m >= %(min_elevation_m)s" in executed_query
    assert "elevation_m <= %(max_elevation_m)s" in executed_query

    assert executed_params == {
        "request_id": str(request_id),
        "profile_type": ProfileType.TRANSVERSE,
        "profile_key": "radius:100.0",
        "min_distance_m": 50.0,
        "max_distance_m": 150.0,
        "min_elevation_m": 110.0,
        "max_elevation_m": 130.0,
        "limit": 25,
        "offset": 5,
    }


def test_get_points_builds_query_without_optional_filters() -> None:
    request_id = uuid4()
    client = _FakeClickHouseClient([])
    warehouse = ClickHouseProfilePointWarehouse(client=client, database="analytics")

    rows = warehouse.get_points(
        request_id=request_id,
        profile_type=None,
        filters=ProfilePointFilters(),
        limit=10,
        offset=0,
    )

    assert rows == []
    assert len(client.query_calls) == 1

    executed_query = client.query_calls[0]["query"]
    executed_params = client.query_calls[0]["parameters"]

    assert "WHERE request_id = %(request_id)s" in executed_query
    assert "profile_type = %(profile_type)s" not in executed_query
    assert "profile_key = %(profile_key)s" not in executed_query
    assert "distance_m >= %(min_distance_m)s" not in executed_query
    assert "distance_m <= %(max_distance_m)s" not in executed_query
    assert "elevation_m >= %(min_elevation_m)s" not in executed_query
    assert "elevation_m <= %(max_elevation_m)s" not in executed_query

    assert executed_params == {
        "request_id": str(request_id),
        "limit": 10,
        "offset": 0,
    }
