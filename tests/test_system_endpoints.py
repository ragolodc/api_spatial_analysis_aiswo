_API_V1_PREFIX = "/api/v1"


def test_health_endpoint_returns_ok(client) -> None:
    response = client.get(f"{_API_V1_PREFIX}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_landing_page_includes_discovery_links(client) -> None:
    response = client.get(f"{_API_V1_PREFIX}/")

    assert response.status_code == 200
    body = response.json()
    hrefs = [link["href"] for link in body["links"]]
    assert "/collections" in hrefs
    assert "/processes" in hrefs


def test_collections_endpoint_lists_available_collections(client) -> None:
    response = client.get(f"{_API_V1_PREFIX}/collections")

    assert response.status_code == 200
    ids = [collection["id"] for collection in response.json()["collections"]]
    assert ids == ["zones", "zone-analyses", "zone-contours"]


def test_processes_endpoint_lists_core_processes(client) -> None:
    response = client.get(f"{_API_V1_PREFIX}/processes")

    assert response.status_code == 200
    ids = [process["id"] for process in response.json()["processes"]]
    assert ids == [
        "highest-point",
        "point-elevation",
        "analyze-zone-elevation",
        "generate-zone-contours",
    ]
