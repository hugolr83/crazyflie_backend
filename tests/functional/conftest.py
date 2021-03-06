from typing import Final, Generator
from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from backend.app import app
from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.crazyflie_drone_link import CrazyflieDroneLink
from backend.models.drone import DroneBattery, DroneRange, DroneState, DroneVec3, DroneOrientation
from backend.registered_drone import RegisteredDrone
from backend.registry import Registry

ARGOS_ID: Final = 1
CRAZYFLIE_ID: Final = 2


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    yield TestClient(app)


@pytest.fixture()
def mocked_argos_link() -> Generator[MagicMock, None, None]:
    yield MagicMock(spec=ArgosDroneLink)


@pytest.fixture()
def mocked_crazyflie_link() -> Generator[MagicMock, None, None]:
    yield MagicMock(spec=CrazyflieDroneLink)


@pytest.fixture()
def registry_mock(mocked_argos_link: MagicMock, mocked_crazyflie_link: MagicMock) -> Generator[Registry, None, None]:
    argos_drone = RegisteredDrone(
        ARGOS_ID,
        mocked_argos_link,
        DroneState.NOT_READY,
        DroneBattery(charge_percentage=2, voltage=3.4),
        DroneVec3(x=1.2, y=3.6, z=2.53),
        DroneOrientation(yaw=40.0),
        DroneRange(front=412312, back=1223, up=134, left=2, right=18, bottom=181),
    )
    crazyflie_drone = RegisteredDrone(
        CRAZYFLIE_ID,
        mocked_crazyflie_link,
        DroneState.CRASHED,
        DroneBattery(charge_percentage=90, voltage=4.1),
        DroneVec3(x=99.1, y=1919.2, z=3.2),
        DroneOrientation(yaw=40.0),
        DroneRange(front=42661, back=123242, up=734, left=90, right=178, bottom=922),
    )
    mocked_registry = Registry(
        drones={
            ARGOS_ID: argos_drone,
            CRAZYFLIE_ID: crazyflie_drone,
        }
    )
    yield mocked_registry
