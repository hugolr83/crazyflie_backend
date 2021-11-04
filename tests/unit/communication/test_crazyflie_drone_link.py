import asyncio
import struct
from asyncio import AbstractEventLoop, Event
from typing import AsyncGenerator, Final, Generator
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from cflib.crazyflie import Appchannel, Console, Crazyflie, Log
from cflib.crazyflie.log import LogConfig
from cflib.utils.callbacks import Caller

from backend.communication.command import Command
from backend.communication.crazyflie_drone_link import CrazyflieDroneLink
from backend.communication.drone_link import InboundLogMessageCallable
from backend.exceptions.communication import CrazyflieCommunicationException

# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


CRAZYFLIE_URI: Final = "radio://0/80/2M/6969696969"


@pytest.fixture
def wait_mock() -> Generator[MagicMock, None, None]:
    with patch.object(Event, "wait") as mocked_wait:
        yield mocked_wait


@pytest.fixture()
def log_config_mock() -> Generator[MagicMock, None, None]:
    with patch("backend.communication.crazyflie_drone_link.generate_log_configs") as mocked_generate_log_configs:
        log_config_mock = MagicMock(spec=LogConfig)
        type(log_config_mock).data_received_cb = PropertyMock(spec=Caller)
        mocked_generate_log_configs.return_value = iter([log_config_mock])
        yield log_config_mock


@pytest.fixture
def crazyflie_mock() -> Generator[MagicMock, None, None]:
    with patch("backend.communication.crazyflie_drone_link.Crazyflie", autospec=Crazyflie) as mocked_crazyflie:
        # Annoying and ugly way to set properties, but Python mocking is what it is
        # See: https://docs.python.org/3/library/unittest.mock.html#autospeccing
        mocked_crazyflie().appchannel = MagicMock(spec=Appchannel)
        mocked_crazyflie().connected = MagicMock(spec=Caller)
        mocked_crazyflie().connection_failed = MagicMock(spec=Caller)
        mocked_crazyflie().connection_lost = MagicMock(spec=Caller)
        mocked_crazyflie().console = MagicMock(spec=Console)
        mocked_crazyflie().console.receivedChar = MagicMock(spec=Caller)
        mocked_crazyflie().disconnected = MagicMock(spec=Caller)
        mocked_crazyflie().log = MagicMock(spec=Log)
        mocked_crazyflie.reset_mock()
        yield mocked_crazyflie


@pytest.fixture()
async def crazyflie_link_mock(
    crazyflie_mock: MagicMock, wait_mock: MagicMock, log_config_mock: MagicMock
) -> AsyncGenerator[CrazyflieDroneLink, None]:
    yield await CrazyflieDroneLink.create(CRAZYFLIE_URI, MagicMock(spec=InboundLogMessageCallable))


async def test_crazyflie_drone_is_initiated(
    crazyflie_mock: MagicMock, wait_mock: MagicMock, log_config_mock: MagicMock
) -> None:
    crazyflie_link = await CrazyflieDroneLink.create(CRAZYFLIE_URI, MagicMock(spec=InboundLogMessageCallable))

    crazyflie_link.crazyflie.connected.add_callback.assert_called()
    crazyflie_link.crazyflie.disconnected.add_callback.assert_called()
    crazyflie_link.crazyflie.connection_failed.add_callback.assert_called()
    crazyflie_link.crazyflie.connection_lost.add_callback.assert_called()
    crazyflie_link.crazyflie.console.receivedChar.add_callback.assert_called()
    log_config_mock.data_received_cb.add_callback.assert_called()
    crazyflie_link.crazyflie.open_link.assert_called()
    wait_mock.assert_awaited()
    crazyflie_link.crazyflie.log.add_config.assert_called_with(log_config_mock)
    log_config_mock.start.assert_called()


async def test_initiate_raise_on_connection_timeout(
    crazyflie_mock: MagicMock, wait_mock: MagicMock, log_config_mock: MagicMock
) -> None:
    wait_mock.side_effect = asyncio.TimeoutError

    with pytest.raises(CrazyflieCommunicationException):
        await CrazyflieDroneLink.create(CRAZYFLIE_URI, MagicMock(spec=InboundLogMessageCallable))


@patch("shutil.rmtree")
async def test_crazyflie_drone_is_terminated(
    rm_tree_mock: MagicMock, crazyflie_link_mock: MagicMock, log_config_mock: MagicMock
) -> None:
    await crazyflie_link_mock.terminate()

    log_config_mock.stop.assert_called()
    crazyflie_link_mock.crazyflie.close_link.assert_called()
    rm_tree_mock.assert_called()


async def test_set_connection_when_connected(crazyflie_link_mock: MagicMock) -> None:
    connection_established_event = Event()
    crazyflie_link_mock.connection_established = connection_established_event

    crazyflie_link_mock._on_connected(CRAZYFLIE_URI, asyncio.get_running_loop())

    await asyncio.wait_for(connection_established_event.wait(), 1)


@patch("backend.communication.crazyflie_drone_link.logger.warning")
async def test_log_on_received_char(logger_mock: MagicMock, crazyflie_link_mock: MagicMock) -> None:
    crazyflie_link_mock._on_received_char("text")

    logger_mock.assert_called()


async def test_clear_connection_when_connection_failed(crazyflie_link_mock: CrazyflieDroneLink) -> None:
    connection_established_event = Event()
    crazyflie_link_mock.connection_established = connection_established_event
    loop_mock = MagicMock(spec=AbstractEventLoop)

    crazyflie_link_mock._on_connection_failed(CRAZYFLIE_URI, "msg", loop_mock)

    loop_mock.call_soon_threadsafe.assert_called_with(connection_established_event.clear)


async def test_clear_connection_when_connection_is_lost(crazyflie_link_mock: CrazyflieDroneLink) -> None:
    connection_established_event = Event()
    crazyflie_link_mock.connection_established = connection_established_event
    loop_mock = MagicMock(spec=AbstractEventLoop)

    crazyflie_link_mock._on_connection_lost(CRAZYFLIE_URI, "msg", loop_mock)

    loop_mock.call_soon_threadsafe.assert_called_with(connection_established_event.clear)


async def test_clear_connection_on_disconnect(crazyflie_link_mock: CrazyflieDroneLink) -> None:
    connection_established_event = Event()
    crazyflie_link_mock.connection_established = connection_established_event
    loop_mock = MagicMock(spec=AbstractEventLoop)

    crazyflie_link_mock._on_disconnected(CRAZYFLIE_URI, loop_mock)

    loop_mock.call_soon_threadsafe.assert_called_with(connection_established_event.clear)


async def test_incoming_message_callable_is_called_on_message(
    crazyflie_mock: MagicMock, crazyflie_link_mock: CrazyflieDroneLink, log_config_mock: MagicMock
) -> None:
    timestamp = 123
    data = {"mayday": "the_drone_is_one_fire"}
    crazyflie_link_mock.on_inbound_log_message = AsyncMock()

    crazyflie_link_mock._on_incoming_log_message(timestamp, data, log_config_mock, asyncio.get_running_loop())

    await asyncio.sleep(0.1)
    crazyflie_link_mock.on_inbound_log_message.assert_awaited()


@pytest.mark.parametrize("command", [command for command in Command])
async def test_send_command(command: Command, crazyflie_link_mock: CrazyflieDroneLink) -> None:
    event = Event()
    event.set()
    crazyflie_link_mock.connection_established = event

    await crazyflie_link_mock.send_command(command)

    crazyflie_link_mock.crazyflie.appchannel.send_packet.assert_called_with(data=struct.pack("I", command.value))
