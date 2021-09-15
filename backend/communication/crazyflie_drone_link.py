from __future__ import annotations

import asyncio
from asyncio import AbstractEventLoop, Event, Queue
from dataclasses import dataclass
from functools import partial
from typing import Any, Final

from cflib.crazyflie import Crazyflie
from fastapi.logger import logger

from backend.communication.drone_link import DroneLink, Message


CRAZYFLIE_CONNECTION_TIMEOUT: Final = 10


@dataclass
class CrazyflieDroneLink(DroneLink):
    crazyflie: Crazyflie
    uri: str
    connection_established: Event
    _inbound_queue: Queue[Message]

    @classmethod
    async def create(cls, uri: str, inbound_queue: Queue[Message]) -> CrazyflieDroneLink:
        link = cls(Crazyflie(), uri, Event(), inbound_queue)
        await link.initiate()
        return link

    async def initiate(self) -> None:
        # We need to call get_running_loop() here and not within the callback as there is no running loop in the thread
        # processing incoming Crazyflie messages. By using run_coroutine_threadsafe, it also schedule the callback in
        # the main event loop which also allow manipulating non threadsafe asyncio objects
        loop = asyncio.get_running_loop()
        self.crazyflie.connected.add_callback(partial(self._on_connected, loop=loop))
        self.crazyflie.disconnected.add_callback(partial(self._on_disconnected, loop=loop))
        self.crazyflie.connection_failed.add_callback(partial(self._on_connection_failed, loop=loop))
        self.crazyflie.connection_lost.add_callback(partial(self._on_connection_lost, loop=loop))
        self.crazyflie.appchannel.packet_received.add_callback(partial(self._on_incoming_message, loop=loop))
        await asyncio.to_thread(self.crazyflie.open_link, self.uri)

    def _on_connected(self, link_uri: str, loop: AbstractEventLoop) -> None:
        logger.error(f"Crazyflie {link_uri} is connected")
        loop.call_soon_threadsafe(self.connection_established.set)

    # TODO: handle disconnections and connection error
    def _on_connection_failed(self, link_uri: str, msg: Any, loop: AbstractEventLoop) -> None:
        logger.error(f"Connection to {link_uri} failed: {msg}")
        loop.call_soon_threadsafe(self.connection_established.clear)

    def _on_connection_lost(self, link_uri: str, msg: Any, loop: AbstractEventLoop) -> None:
        logger.error(f"Connection to {link_uri} lost: {msg}")
        loop.call_soon_threadsafe(self.connection_established.clear)

    def _on_disconnected(self, link_uri: str, loop: AbstractEventLoop) -> None:
        logger.error(f"Crazyflie {link_uri} is disconnected")
        loop.call_soon_threadsafe(self.connection_established.clear)

    def _on_incoming_message(self, packet: bytes, loop: AbstractEventLoop) -> None:
        asyncio.run_coroutine_threadsafe(self.inbound_queue.put(Message.from_bytes(packet)), loop)

    async def send_message(self, message: Message) -> None:
        await asyncio.wait_for(self.connection_established.wait(), timeout=CRAZYFLIE_CONNECTION_TIMEOUT)
        await asyncio.to_thread(self.crazyflie.appchannel.send_packet, message.serialize())

    @property
    def inbound_queue(self) -> Queue[Message]:
        return self._inbound_queue
