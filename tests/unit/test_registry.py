from typing import Generator
from unittest.mock import MagicMock

import pytest

from backend.communication.drone_link import DroneLink
from backend.registered_drone import RegisteredDrone
from backend.registry import get_registry

# All test coroutines will be treated as marked
from backend.tasks.backend_task import BackendTask

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def clear_registry_cache() -> Generator[None, None, None]:
    get_registry.cache_clear()
    yield


def test_registry_is_cached() -> None:
    assert get_registry() == get_registry()


async def test_queues_are_initialized_and_retrieved() -> None:
    registry = get_registry()

    with pytest.raises(AssertionError):
        _ = registry.inbound_log_queue

    await registry.initialize_queues()

    _ = registry.inbound_log_queue


def test_drones_are_registered_and_unregistered() -> None:
    registry = get_registry()
    registered_drone = RegisteredDrone("uuid", MagicMock(spec=DroneLink))

    assert not registry.drones

    registry.register_drone(registered_drone)

    assert registry.drones

    registry.unregister_drone(registered_drone)

    assert not registry.drones


def test_tasks_are_registered_and_unregistered() -> None:
    registry = get_registry()
    task = MagicMock(spec=BackendTask)

    assert not registry.backend_tasks

    registry.register_task(task)

    assert registry.backend_tasks

    registry.unregister_task(task)

    assert not registry.backend_tasks
