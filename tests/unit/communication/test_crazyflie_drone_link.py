from asyncio import Event
from functools import partial
from time import sleep
from typing import Final, Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from cflib.crazyflie import Console, Crazyflie, Log
from cflib.crazyflie.log import LogConfig
from cflib.utils.callbacks import Caller

from backend.communication.crazyflie_drone_link import CrazyflieDroneLink
from backend.communication.drone_link import InboundLogMessageCallable

# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


CRAZYFLIE_URI: Final = "radio://0/80/2M/6969696969"


@pytest.fixture
def crazyflie_mock() -> Generator[MagicMock, None, None]:
    with patch("backend.communication.crazyflie_drone_link.Crazyflie", autospec=Crazyflie) as mocked_crazyflie:
        # Annoying and ugly way to set properties, but Python mocking is what it is
        # See: https://docs.python.org/3/library/unittest.mock.html#autospeccing
        mocked_crazyflie().connected = MagicMock(spec=Caller)
        mocked_crazyflie().disconnected = MagicMock(spec=Caller)
        mocked_crazyflie().connection_failed = MagicMock(spec=Caller)
        mocked_crazyflie().connection_lost = MagicMock(spec=Caller)
        mocked_crazyflie().console = MagicMock(spec=Console)
        mocked_crazyflie().console.receivedChar = MagicMock(spec=Caller)
        mocked_crazyflie().log = MagicMock(spec=Log)
        mocked_crazyflie.reset_mock()
        yield mocked_crazyflie


@pytest.fixture
def wait_mock() -> Generator[MagicMock, None, None]:
    with patch.object(Event, "wait") as mocked_wait:
        yield mocked_wait


@pytest.fixture()
def generate_log_configs_mock() -> Generator[MagicMock, None, None]:
    with patch("backend.communication.crazyflie_drone_link.generate_log_configs") as mocked_generate_log_configs:
        log_config_mock = MagicMock(spec=LogConfig)
        type(log_config_mock).data_received_cb = PropertyMock(spec=Caller)
        mocked_generate_log_configs.return_value = iter([])
        yield mocked_generate_log_configs


async def test_crazyflie_drone_is_initiated(
    crazyflie_mock: MagicMock, wait_mock: MagicMock, generate_log_configs_mock: MagicMock
) -> None:
    crazyflie_link = await CrazyflieDroneLink.create(CRAZYFLIE_URI, MagicMock(spec=InboundLogMessageCallable))
