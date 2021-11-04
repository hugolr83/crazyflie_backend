import struct
from asyncio import CancelledError, StreamReader, StreamWriter, Task
from typing import Final, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.command import Command
from backend.communication.drone_link import InboundLogMessageCallable
from backend.exceptions.communication import ArgosCommunicationException

# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


@pytest.fixture()
def connection_mock() -> Generator[MagicMock, None, None]:
    with patch("asyncio.open_connection") as patched_open_connection:
        open_connection_mock = AsyncMock(return_value=(MagicMock(spec=StreamReader), MagicMock(spec=StreamWriter)))
        patched_open_connection.side_effect = open_connection_mock
        yield patched_open_connection


@pytest.fixture()
def create_task_mock() -> Generator[MagicMock, None, None]:
    with patch("asyncio.create_task") as patched_create_task:
        patched_create_task.return_value = MagicMock(spec=Task)
        yield patched_create_task


ARGOS_ENDPOINT: Final = "argos"
ARGOS_PORT: Final = 6969


async def test_argos_drone_link_is_initiated(connection_mock: MagicMock, create_task_mock: MagicMock) -> None:
    on_inbound_message_callable = MagicMock(spec=InboundLogMessageCallable)

    with patch.object(ArgosDroneLink, "process_incoming_message", return_value=AsyncMock()):
        result = await ArgosDroneLink.create(ARGOS_ENDPOINT, ARGOS_PORT, on_inbound_message_callable)

    assert result.argos_endpoint == ARGOS_ENDPOINT
    assert result.argos_port == ARGOS_PORT
    assert isinstance(result.reader, StreamReader)
    assert isinstance(result.writer, StreamWriter)
    assert callable(on_inbound_message_callable)

    connection_mock.assert_called()
    create_task_mock.assert_called()


async def test_argos_drone_link_raise_on_connection_error(
    connection_mock: MagicMock, create_task_mock: MagicMock
) -> None:
    connection_mock.side_effect = OSError

    with patch.object(ArgosDroneLink, "process_incoming_message", return_value=AsyncMock()), pytest.raises(
        ArgosCommunicationException
    ):
        await ArgosDroneLink.create(ARGOS_ENDPOINT, ARGOS_PORT, MagicMock(spec=InboundLogMessageCallable))


@pytest.mark.parametrize("with_task", [True, False])
async def test_resources_are_liberated_on_termination(with_task: bool) -> None:
    task_mock = MagicMock(spec=Task) if with_task else None
    writer_mock = MagicMock(spec=StreamWriter)

    drone_link = ArgosDroneLink(
        ARGOS_ENDPOINT,
        ARGOS_PORT,
        MagicMock(spec=StreamReader),
        writer_mock,
        MagicMock(spec=InboundLogMessageCallable),
        task_mock,
    )
    await drone_link.terminate()

    if with_task:
        assert task_mock
        task_mock.cancel.assert_called()
    writer_mock.close.assert_called()


async def test_incoming_messages_are_processed() -> None:
    reader_mock = MagicMock(spec=StreamReader)
    expected_message = b"ABC\n"
    reader_mock.readline.side_effect = (expected_message, CancelledError)
    on_incoming_message_callable = AsyncMock(spec=InboundLogMessageCallable)

    drone_link = ArgosDroneLink(
        ARGOS_ENDPOINT,
        ARGOS_PORT,
        reader_mock,
        MagicMock(spec=StreamWriter),
        on_incoming_message_callable,
        None,
    )

    await drone_link.process_incoming_message()
    on_incoming_message_callable.assert_awaited_with(data=expected_message)


@pytest.mark.parametrize("command", [command for command in Command])
async def test_commands_are_properly_sent(command: Command) -> None:
    writer_mock = MagicMock(spec=StreamWriter)

    drone_link = ArgosDroneLink(
        ARGOS_ENDPOINT,
        ARGOS_PORT,
        MagicMock(spec=StreamReader),
        writer_mock,
        MagicMock(spec=InboundLogMessageCallable),
        None,
    )

    await drone_link.send_command(command)
    writer_mock.write.assert_called_with(struct.pack("Ic", command.value, b"\n"))
    writer_mock.drain.assert_awaited()
