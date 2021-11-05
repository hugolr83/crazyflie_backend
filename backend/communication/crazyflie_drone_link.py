from __future__ import annotations

import asyncio
import shutil
import struct
import tempfile
from asyncio import AbstractEventLoop, Event
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Final

from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from fastapi.logger import logger

from backend.communication.command import Command
from backend.communication.drone_link import DroneLink, InboundLogMessageCallable
from backend.communication.log_message import generate_log_configs
from backend.exceptions.communication import CrazyflieCommunicationException

CRAZYFLIE_CONNECTION_TIMEOUT: Final = 15


@dataclass
class CrazyflieDroneLink(DroneLink):
    crazyflie: Crazyflie
    uri: str
    log_configs: list[LogConfig]
    connection_established: Event
    on_inbound_log_message: InboundLogMessageCallable
    on_debug_log_message: InboundLogMessageCallable
    rw_cache: Path

    @classmethod
    async def create(
        cls,
        uri: str,
        on_inbound_log_message: InboundLogMessageCallable,
        on_debug_log_message: InboundLogMessageCallable,
    ) -> CrazyflieDroneLink:
        log_configs = list(generate_log_configs())
        rw_cache = Path(tempfile.mkdtemp())
        link = cls(
            Crazyflie(rw_cache=str(rw_cache)),
            uri,
            log_configs,
            Event(),
            on_inbound_log_message,
            on_debug_log_message,
            rw_cache,
        )
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
        self.crazyflie.console.receivedChar.add_callback(partial(self._on_received_char, loop=loop))
        for log_config in self.log_configs:
            log_config.data_received_cb.add_callback(partial(self._on_incoming_log_message, loop=loop))
        await asyncio.to_thread(self.crazyflie.open_link, self.uri)

        try:
            await asyncio.wait_for(self.connection_established.wait(), timeout=CRAZYFLIE_CONNECTION_TIMEOUT)
        except asyncio.TimeoutError as e:
            raise CrazyflieCommunicationException(self.uri) from e

        for log_config in self.log_configs:
            self.crazyflie.log.add_config(log_config)
            await asyncio.to_thread(log_config.start)

    async def terminate(self) -> None:
        for log_config in self.log_configs:
            await asyncio.to_thread(log_config.stop)
        await asyncio.to_thread(self.crazyflie.close_link)
        await asyncio.to_thread(shutil.rmtree, self.rw_cache)

    def _on_connected(self, link_uri: str, loop: AbstractEventLoop) -> None:
        logger.error(f"Crazyflie {link_uri} is connected")
        loop.call_soon_threadsafe(self.connection_established.set)

    def _on_received_char(self, text: str, loop: AbstractEventLoop) -> None:
        logger.warning(f"Log from Crazyflie {self.uri}: {text}")
        asyncio.run_coroutine_threadsafe(self.on_debug_log_message(message=text), loop)

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

    def _on_incoming_log_message(
        self, timestamp: int, data: dict[str, Any], log_config: LogConfig, loop: AbstractEventLoop
    ) -> None:
        asyncio.run_coroutine_threadsafe(
            self.on_inbound_log_message(timestamp=timestamp, data=data, log_config=log_config), loop
        )

    async def send_command(self, command: Command) -> None:
        await asyncio.wait_for(self.connection_established.wait(), timeout=CRAZYFLIE_CONNECTION_TIMEOUT)
        await asyncio.to_thread(self.crazyflie.appchannel.send_packet, data=struct.pack("I", command.value))
