from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.shared.db.session import get_db


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[object, None, None]:
        # Tests use monkeypatched factories; DB object itself is not used.
        yield object()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
