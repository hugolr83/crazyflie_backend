import asyncio
import logging

from coveo_settings import BoolSetting
from starlette.websockets import WebSocket
from wsproto.utilities import LocalProtocolError

from backend.models.drone import Drone
from backend.registry import get_registry

CRAZYFLIE_ENABLE_HEARTBEAT = BoolSetting("crazyflie.enable_heartbeat", fallback=True)


async def send_message_to_socket(socket: WebSocket, drone: Drone) -> None:
    try:
        await socket.send_json(drone.dict())
    except (LocalProtocolError, RuntimeError) as e:
        logging.error(e)


async def process_outbound_drone_pulses() -> None:
    registry = get_registry()
    while drone := await registry.outbound_pulse_queue.get():
        if registry.pulse_sockets:
            await asyncio.gather(*(send_message_to_socket(socket, drone) for socket in registry.pulse_sockets))
