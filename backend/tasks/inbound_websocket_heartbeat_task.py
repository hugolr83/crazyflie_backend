import asyncio
import logging
from typing import Final

from coveo_settings import IntSetting
from starlette.websockets import WebSocket, WebSocketDisconnect
from wsproto.utilities import LocalProtocolError

from backend.registry import get_registry
from backend.tasks.backend_task import BackendTask

HEARTBEAT_TIMEOUT_SECONDS: Final = IntSetting("heartbeat_timeout_seconds", fallback=10)


class InboundWebsocketHeartbeatTask(BackendTask):
    def __init__(self, socket: WebSocket) -> None:
        self.socket = socket
        super().__init__()

    async def run(self) -> None:
        try:
            registry = get_registry()
            try:
                while await asyncio.wait_for(self.socket.receive(), timeout=int(HEARTBEAT_TIMEOUT_SECONDS)):
                    pass
            except asyncio.TimeoutError:
                logging.warning(f"Websocket on port {self.socket.client.port} timed out")
                await self.socket.close()
                registry.unregister_socket(self.socket)
            except (LocalProtocolError, RuntimeError, WebSocketDisconnect):
                logging.warning(f"Websocket on port {self.socket.client.port} is disconnected")
                registry.unregister_socket(self.socket)
        except asyncio.CancelledError:
            await self.socket.close()
            get_registry().unregister_socket(self.socket)
