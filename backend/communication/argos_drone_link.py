from __future__ import annotations

import asyncio
import struct
from asyncio import CancelledError, StreamReader, StreamWriter, Task
from dataclasses import dataclass
from typing import Optional

from fastapi.logger import logger

from backend.communication.command import Command
from backend.communication.drone_link import DroneLink, InboundLogMessageCallable
from backend.exceptions.communication import ArgosCommunicationException


@dataclass
class ArgosDroneLink(DroneLink):
    argos_endpoint: str
    argos_port: int
    reader: StreamReader
    writer: StreamWriter
    on_inbound_message: InboundLogMessageCallable
    incoming_message_task: Optional[Task] = None

    @classmethod
    async def create(
        cls, argos_endpoint: str, argos_port: int, on_inbound_message: InboundLogMessageCallable
    ) -> ArgosDroneLink:
        try:
            reader, writer = await asyncio.open_connection(argos_endpoint, argos_port)
        except OSError as e:
            raise ArgosCommunicationException(argos_port) from e

        adapter = cls(argos_endpoint, argos_port, reader, writer, on_inbound_message)
        await adapter.initiate()
        return adapter

    async def initiate(self) -> None:
        self.incoming_message_task = asyncio.create_task(self.process_incoming_message())

    async def terminate(self) -> None:
        if self.incoming_message_task:
            self.incoming_message_task.cancel()
        self.writer.close()

    async def process_incoming_message(self) -> None:
        try:
            while data := await self.reader.readline():
                await self.on_inbound_message(data=data)
        except CancelledError:
            logger.exception("Process incoming message task was cancelled")

    async def send_command(self, command: Command) -> None:
        self.writer.write(struct.pack("Ic", command.value, b"\n"))
        await self.writer.drain()
