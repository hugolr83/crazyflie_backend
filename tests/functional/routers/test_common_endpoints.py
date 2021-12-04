from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Final, Generator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from backend.communication.command import Command
from backend.registry import Registry
from tests.functional.conftest import ARGOS_ID, CRAZYFLIE_ID


@pytest.fixture()
def get_registry_mock(registry_mock: Registry) -> Generator[Registry, None, None]:
    with patch("backend.routers.common.get_registry") as patched_get_registry:
        patched_get_registry.return_value = registry_mock
        yield registry_mock


@dataclass
class GetDronesTestCase:
    url_parameter: str
    expected_response: list[dict[str, Any]]


ARGOS_DRONE_RESPONSE: Final = {
    "id": ARGOS_ID,
    "state": "NOT READY",
    "type": "ARGOS",
    "battery": {"charge_percentage": 2},
    "position": {"x": 1.2, "y": 3.6, "z": 2.53},
    "orientation": {"yaw": 40.0},
    "range": {"front": 412312, "back": 1223, "up": 134, "left": 2, "right": 18, "bottom": 181},
    "total_distance": 0.0,
}

CRAZYFLIE_DRONE_RESPONSE: Final = {
    "id": CRAZYFLIE_ID,
    "state": "CRASHED",
    "type": "CRAZYFLIE",
    "battery": {"charge_percentage": 90},
    "position": {"x": 99.1, "y": 1919.2, "z": 3.2},
    "orientation": {"yaw": 40.0},
    "range": {"front": 42661, "back": 123242, "up": 734, "left": 90, "right": 178, "bottom": 922},
    "total_distance": 0.0,
}


@pytest.mark.parametrize(
    "test_case",
    [
        GetDronesTestCase("", [ARGOS_DRONE_RESPONSE, CRAZYFLIE_DRONE_RESPONSE]),
        GetDronesTestCase("?drone_type=ARGOS", [ARGOS_DRONE_RESPONSE]),
        GetDronesTestCase("?drone_type=CRAZYFLIE", [CRAZYFLIE_DRONE_RESPONSE]),
    ],
)
def test_get_all_drones(get_registry_mock: Registry, test_case: GetDronesTestCase, test_client: TestClient) -> None:
    response = test_client.get(f"/drones{test_case.url_parameter}")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == test_case.expected_response


@dataclass()
class UpdateDroneTestCase:
    endpoint: str
    command: Command
