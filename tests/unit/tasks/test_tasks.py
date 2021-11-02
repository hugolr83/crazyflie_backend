from typing import Generator, Type
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.registry import Registry
from backend.tasks.backend_task import BackendTask
from backend.tasks.tasks import initiate_tasks, terminate_tasks

# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


class StubTask(BackendTask):
    async def run(self) -> None:
        pass


@pytest.fixture()
def mocked_task() -> Generator[Type[StubTask], None, None]:
    stubed_task = StubTask
    stubed_task.initiate = AsyncMock()  # type: ignore[assignment]
    stubed_task.terminate = AsyncMock()  # type: ignore[assignment]
    with patch("backend.tasks.tasks.TASKS_TO_INITIALIZE", [stubed_task]):
        yield stubed_task


@pytest.fixture()
def mocked_registry(mocked_task: Type[StubTask]) -> Generator[MagicMock, None, None]:
    with patch("backend.tasks.tasks.get_registry") as patched_registry:
        registry_mock = MagicMock(spec=Registry)
        registry_mock.backend_tasks = [mocked_task]
        patched_registry.return_value = registry_mock
        yield registry_mock


async def test_tasks_are_initiated(mocked_task: Type[StubTask], mocked_registry: MagicMock) -> None:
    await initiate_tasks()

    mocked_task.initiate.assert_awaited()  # type: ignore[attr-defined]
    mocked_registry.register_task.assert_called()


async def test_tasks_are_terminated(mocked_task: Type[StubTask], mocked_registry: MagicMock) -> None:
    await terminate_tasks()

    mocked_task.terminate.assert_called()  # type: ignore[attr-defined]
