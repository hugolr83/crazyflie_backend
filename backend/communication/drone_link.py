from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import Queue

from backend.communication.message import Message


class DroneLink(ABC):
    @abstractmethod
    async def initiate(self) -> None:
        ...

    @abstractmethod
    async def send_message(self, message: Message) -> None:
        ...

    @property
    @abstractmethod
    def inbound_queue(self) -> Queue[Message]:
        ...
