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
    async def send_command(self, command: Command) -> None:
        ...  # pragma: no cover

    @abstractmethod
    async def send_command_with_payload(self, command: Command, payload: bytes) -> None:
        ...  # pragma: no cover
