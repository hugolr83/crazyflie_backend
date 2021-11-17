from __future__ import annotations

import asyncio
import struct
from asyncio import CancelledError, Event, StreamReader, StreamWriter, Task
from dataclasses import dataclass
from typing import Optional

from fastapi.logger import logger

from backend.communication.command import Command
from backend.communication.drone_link import DroneLink, InboundLogMessageCallable


@dataclass
class ArgosDroneLink(DroneLink):
    argos_endpoint: str
    argos_port: int
    reader: Optional[StreamReader]
    writer: Optional[StreamWriter]
    on_inbound_message: InboundLogMessageCallable
    connection_established: Event
    incoming_message_task: Optional[Task] = None

    @classmethod
    async def create(
        cls, argos_endpoint: str, argos_port: int, on_inbound_message: InboundLogMessageCallable
    ) -> ArgosDroneLink:
        try:
            reader, writer = await asyncio.open_connection(argos_endpoint, argos_port)
        except OSError as e:
            logger.error(e)
            reader, writer = None, None  # type: ignore[assignment]

        adapter = cls(argos_endpoint, argos_port, reader, writer, on_inbound_message, Event())
        await adapter.initiate()
        return adapter

    async def initiate(self) -> None:
        self.incoming_message_task = asyncio.create_task(self.process_incoming_message())

    async def reconnect(self) -> None:
        pass

    async def terminate(self) -> None:
        if self.incoming_message_task:
            self.incoming_message_task.cancel()
        if self.writer:
            self.writer.close()
            self.writer = None
        self.reader = None

    async def process_incoming_message(self) -> None:
        self.connection_established.set()
        try:
            assert self.reader, "Reader must be defined"
            while data := await self.reader.readline():
                await self.on_inbound_message(data=data)
        except CancelledError:
            logger.exception("Process incoming message task was cancelled")
        finally:
            self.connection_established.clear()

    async def send_command(self, command: Command) -> None:
        assert self.writer, "Writer must be defined"
        self.writer.write(struct.pack("Ic", command.value, b"\n"))
        await self.writer.drain()

    @property
    def is_connected(self) -> bool:
        return self.connection_established.is_set()
