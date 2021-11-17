from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine

from backend.communication.command import Command

InboundLogMessageCallable = Callable[..., Coroutine[Any, Any, None]]


class DroneLink(ABC):
    @abstractmethod
    async def initiate(self) -> None:
        ...  # pragma: no cover

    @abstractmethod
    async def terminate(self) -> None:
        ...  # pragma: no cover

    @abstractmethod
    async def reconnect(self) -> None:
        ...  # pragma: no cover

    @abstractmethod
    async def send_command(self, command: Command) -> None:
        ...  # pragma: no cover

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        ...  # pragma: no cover
