from asyncio import Task
from typing import Awaitable
from unittest.mock import MagicMock, patch

import pytest

from backend.tasks.backend_task import BackendTask

# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


class BackgroundTaskStub(BackendTask):
    async def run(self) -> None:
        pass


@patch("asyncio.create_task")
async def test_backend_tasks_are_initiated(create_task_mock: MagicMock) -> None:
    task = BackgroundTaskStub()

    await task.initiate()

    create_task_mock.assert_called()


async def test_backend_tasks_are_terminated() -> None:
    task = BackgroundTaskStub()
    task_mock = MagicMock(spec=Task)
    task.task = task_mock

    await task.terminate()

    await task.run()
    task_mock.cancel.assert_called()
