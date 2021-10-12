import asyncio
import logging
from typing import Final

from starlette.websockets import WebSocket, WebSocketDisconnect
from wsproto.utilities import LocalProtocolError

from backend.registry import get_registry

HEARTBEAT_TIMEOUT_SECONDS: Final = 10


async def process_inbound_heartbeat(socket: WebSocket) -> None:
    registry = get_registry()
    try:
        while await asyncio.wait_for(socket.receive(), timeout=HEARTBEAT_TIMEOUT_SECONDS):
            pass
    except asyncio.TimeoutError:
        logging.warning(f"Websocket on port {socket.client.port} timed out")
        await socket.close()
    except (LocalProtocolError, RuntimeError, WebSocketDisconnect):
        logging.warning(f"Websocket on port {socket.client.port} is disconnected")
    finally:
        await registry.unregister_socket(socket)
