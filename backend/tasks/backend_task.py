import asyncio
from abc import ABC, abstractmethod
from asyncio import Task
from typing import Optional


class BackendTask(ABC):
    def __init__(self) -> None:
        self.task: Optional[Task] = None

    async def initiate(self) -> None:
        self.task = asyncio.create_task(self.run())

    @abstractmethod
    async def run(self) -> None:
        ...  # pragma: no cover

    async def terminate(self) -> None:
        if self.task:
            self.task.cancel()
            self.task = None
