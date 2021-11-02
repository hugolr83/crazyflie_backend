from itertools import count, islice
from logging import Logger
from typing import Final, Generator
from unittest.mock import MagicMock, call, patch
from uuid import UUID

import pytest
from coveo_settings.mock import mock_config_value

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.communication import (
    ARGOS_DRONES_STARTING_PORT,
    ARGOS_NUMBER_OF_DRONES,
    CRAZYFLIE_ADDRESSES,
    initiate_argos_drone_link,
    initiate_crazyflie_drone_link,
    initiate_links,
    terminate_links,
)
from backend.communication.crazyflie_drone_link import CrazyflieDroneLink
from backend.exceptions.communication import CrazyflieCommunicationException
from backend.registered_drone import RegisteredDrone
from backend.registry import Registry

# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


@pytest.fixture()
def registry_mock() -> Generator[MagicMock, None, None]:
    with patch("backend.communication.communication.get_registry") as get_registry_mock:
        mocked_registry = MagicMock(spec=Registry)
        get_registry_mock.return_value = mocked_registry
        yield mocked_registry


@pytest.fixture()
def crtp_mock() -> Generator[MagicMock, None, None]:
    with patch("backend.communication.communication.crtp", autospec=True) as mocked_crtp:
        yield mocked_crtp


DRONE_PORT: Final = 6969


def assert_drone_is_registered(mocked_drone_link: MagicMock, registry_mock: MagicMock) -> None:
    registry_mock.register_drone.assert_called()
    assert isinstance(registry_mock.register_drone.call_args.args[0], RegisteredDrone)
    assert UUID(registry_mock.register_drone.call_args.args[0].uuid)
    assert registry_mock.register_drone.call_args.args[0].link == mocked_drone_link


@patch.object(ArgosDroneLink, "create")
async def test_initiate_argos_drone_link(create_argos_drone_mock: MagicMock, registry_mock: MagicMock) -> None:
    mocked_argos_drone_link = MagicMock(spec=ArgosDroneLink)
    create_argos_drone_mock.return_value = mocked_argos_drone_link

    await initiate_argos_drone_link(drone_port=DRONE_PORT)

    create_argos_drone_mock.assert_awaited()
    assert isinstance(create_argos_drone_mock.call_args.args[0], str)
    assert create_argos_drone_mock.call_args.args[1] == DRONE_PORT
    assert callable(create_argos_drone_mock.call_args.args[2])
    assert_drone_is_registered(mocked_argos_drone_link, registry_mock)


@patch.object(CrazyflieDroneLink, "create")
async def test_initiate_crazyflie_drone_link(
    create_crazyflie_drone_mock: MagicMock, crtp_mock: MagicMock, registry_mock: MagicMock
) -> None:
    expected_drone_uri = "radio://0/80/2M/6969696969"
    crtp_mock.scan_interfaces.return_value = [[expected_drone_uri], [None]]
    mocked_crazyflie_drone_link = MagicMock(spec=CrazyflieDroneLink)
    create_crazyflie_drone_mock.return_value = mocked_crazyflie_drone_link

    await initiate_crazyflie_drone_link(0x6969696969)

    create_crazyflie_drone_mock.assert_awaited()
    assert create_crazyflie_drone_mock.call_args.args[0] == expected_drone_uri
    assert callable(create_crazyflie_drone_mock.call_args.args[1])
    assert_drone_is_registered(mocked_crazyflie_drone_link, registry_mock)


async def test_initiate_crazyflie_drone_link_raise_when_drone_not_found(crtp_mock: MagicMock) -> None:
    crtp_mock.scan_interfaces.return_value = [[], []]

    with pytest.raises(CrazyflieCommunicationException):
        await initiate_crazyflie_drone_link(0x6969696969)


async def test_links_are_initiated(crtp_mock: MagicMock, registry_mock: MagicMock) -> None:
    argos_starting_port = 3995
    argos_number_of_drones = 2

    with patch(
        "backend.communication.communication.initiate_argos_drone_link"
    ) as initiate_argos_drone_link_mock, patch(
        "backend.communication.communication.initiate_crazyflie_drone_link"
    ) as intiate_crazyflie_drone_link_mock, patch.object(
        Logger, "error"
    ) as logger_error_mock, mock_config_value(
        ARGOS_DRONES_STARTING_PORT, value=argos_starting_port
    ), mock_config_value(
        ARGOS_NUMBER_OF_DRONES, value=argos_number_of_drones
    ):
        await initiate_links()

        crtp_mock.init_drivers.assert_called()
        assert initiate_argos_drone_link_mock.await_args_list == [
            call(port) for port in islice(count(argos_starting_port), argos_number_of_drones)
        ]
        assert intiate_crazyflie_drone_link_mock.await_args_list == [call(address) for address in CRAZYFLIE_ADDRESSES]
        logger_error_mock.assert_not_called()


async def test_initiate_links_logs_exceptions(crtp_mock: MagicMock, registry_mock: MagicMock) -> None:
    argos_starting_port = 3995
    argos_number_of_drones = 2

    with patch(
        "backend.communication.communication.initiate_argos_drone_link"
    ) as initiate_argos_drone_link_mock, patch(
        "backend.communication.communication.initiate_crazyflie_drone_link"
    ), patch.object(
        Logger, "error"
    ) as logger_error_mock, mock_config_value(
        ARGOS_DRONES_STARTING_PORT, value=argos_starting_port
    ), mock_config_value(
        ARGOS_NUMBER_OF_DRONES, value=argos_number_of_drones
    ):
        initiate_argos_drone_link_mock.side_effect = Exception(":panic:")

        await initiate_links()

        logger_error_mock.assert_called()


async def test_links_are_terminated(registry_mock: MagicMock) -> None:
    argos_link_mock = MagicMock(spec=ArgosDroneLink)
    argos_drone_mock = MagicMock(spec=RegisteredDrone)
    argos_drone_mock.link = argos_link_mock
    crazyflie_link_mock = MagicMock(spec=CrazyflieDroneLink)
    crazyflie_drone_mock = MagicMock(spec=RegisteredDrone)
    crazyflie_drone_mock.link = crazyflie_link_mock
    registry_mock.drones = {"argos": argos_drone_mock, "crazyflie": crazyflie_drone_mock}

    await terminate_links()

    argos_link_mock.terminate.assert_awaited()
    crazyflie_link_mock.terminate.assert_awaited()
