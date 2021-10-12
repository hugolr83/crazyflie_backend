import asyncio
from typing import Final

from coveo_settings import BoolSetting
from starlette.websockets import WebSocket, WebSocketDisconnect

from backend.models.drone import Drone
from backend.registry import get_registry

CRAZYFLIE_ENABLE_HEARTBEAT = BoolSetting("crazyflie.enable_heartbeat", fallback=True)
HEARTBEAT_TIMEOUT_SECONDS: Final = 0.2


async def send_message_to_socket(socket: WebSocket, drone: Drone) -> None:
    try:
        await socket.send_json(drone.dict())
        if bool(CRAZYFLIE_ENABLE_HEARTBEAT):
            await asyncio.wait_for(socket.receive(), timeout=HEARTBEAT_TIMEOUT_SECONDS)
    except (asyncio.TimeoutError, WebSocketDisconnect):
        await get_registry().unregister_socket(socket)


async def process_outbound_drone_pulses() -> None:
    registry = get_registry()
    while drone := await registry.outbound_pulse_queue.get():
        if registry.pulse_sockets:
            await asyncio.gather(*(send_message_to_socket(socket, drone) for socket in registry.pulse_sockets))
