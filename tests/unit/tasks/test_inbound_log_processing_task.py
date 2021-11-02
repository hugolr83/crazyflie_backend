import asyncio
from asyncio import Queue
from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from backend.communication.log_message import LogMessage
from backend.registered_drone import RegisteredDrone
from backend.registry import Registry
from backend.tasks.inbound_log_processing_task import InboundLogProcessingTask

# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


@pytest.fixture()
def mocked_message() -> Generator[MagicMock, None, None]:
    mocked_message = MagicMock(spec=LogMessage)
    type(mocked_message).drone_uuid = PropertyMock(return_value="uuid")
    yield mocked_message


@pytest.fixture()
def inbound_log_queue(mocked_message: MagicMock) -> Generator[MagicMock, None, None]:
    queue_mock = MagicMock(spec=Queue)
    queue_mock.get.side_effect = [mocked_message, asyncio.CancelledError]
    yield queue_mock


@pytest.fixture()
def registry_mock(inbound_log_queue: MagicMock) -> Generator[MagicMock, None, None]:
    with patch("backend.tasks.inbound_log_processing_task.get_registry") as patched_get_registry:
        mocked_registry = MagicMock(spec=Registry)
        mocked_registry.inbound_log_queue = inbound_log_queue
        patched_get_registry.return_value = mocked_registry
        yield mocked_registry


async def test_inbound_log_messages_are_processed(mocked_message: MagicMock, registry_mock: MagicMock) -> None:
    task = InboundLogProcessingTask()
    mocked_drone = MagicMock(spec=RegisteredDrone)
    registry_mock.get_drone.return_value = mocked_drone

    await task.run()

    mocked_drone.update_from_log_message.assert_called_with(mocked_message)


@patch("backend.tasks.inbound_log_processing_task.logger.error")
async def test_inbound_log_messages_continue_on_unknown_drones(
    logger_mock: MagicMock, mocked_message: MagicMock, registry_mock: MagicMock
) -> None:
    task = InboundLogProcessingTask()
    registry_mock.get_drone.return_value = None

    await task.run()

    logger_mock.assert_called()
