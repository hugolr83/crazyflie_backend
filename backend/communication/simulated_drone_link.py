from __future__ import annotations

import asyncio
from asyncio import CancelledError, Queue, StreamReader, StreamWriter
from dataclasses import dataclass

from fastapi.logger import logger

from backend.communication.drone_link import DroneLink, Message


@dataclass
class SimulatedDroneLink(DroneLink):
    reader: StreamReader
    writer: StreamWriter
    _inbound_queue: Queue[Message]

    @classmethod
    async def create(cls, argos_host: str, argos_port: str, inbound_queue: Queue[Message]) -> SimulatedDroneLink:
        reader, writer = await asyncio.open_connection(argos_host, argos_port)
        link = cls(reader, writer, inbound_queue)
        await link.initiate()
        return link

    async def initiate(self) -> None:
        asyncio.create_task(self.process_incoming_message())

    async def send_message(self, message: Message) -> None:
        self.writer.write(message.serialize())

    async def process_incoming_message(self) -> None:
        # TODO: support reconnect when socket is closed
        try:
            while data := await self.reader.readline():
                await self.inbound_queue.put(Message.from_bytes(data))
        except CancelledError:
            logger.exception("Process incoming message task was cancelled")

    @property
    def inbound_queue(self) -> Queue[Message]:
        return self._inbound_queue
