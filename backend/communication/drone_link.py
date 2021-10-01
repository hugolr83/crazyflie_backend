from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Callable, Coroutine
from typing import Any

from backend.communication.command import Command

InboundMessageCallable = Callable[[bytes], Coroutine[Any, Any, None]]


class DroneLink(ABC):
    @abstractmethod
    async def initiate(self) -> None:
        ...

    @abstractmethod
    async def send_command(self, command: Command) -> None:
        ...
