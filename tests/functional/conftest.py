from typing import Generator

import pytest
from starlette.testclient import TestClient

from backend.app import app


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    yield TestClient(app)
