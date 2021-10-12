from asyncio import Queue
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Generator, Optional

from starlette.websockets import WebSocket

from backend.communication.log_message import LogMessage
from backend.models.drone import Drone, DroneType
from backend.registered_drone import RegisteredDrone


@dataclass
class Registry:
    drones: dict[str, RegisteredDrone] = field(default_factory=dict)
    _inbound_log_message_queue: Optional[Queue[LogMessage]] = None
    _output_pulse_queue: Optional[Queue[Drone]] = None
    pulse_sockets: list[WebSocket] = field(default_factory=list)

    def get_drone(self, drone_uuid: str) -> Optional[RegisteredDrone]:
        return self.drones.get(drone_uuid)

    def get_drones(self, drone_type: Optional[DroneType]) -> Generator[RegisteredDrone, None, None]:
        if drone_type:
            yield from self.argos_drones if drone_type == DroneType.ARGOS else self.crazyflie_drones
        else:
            yield from self.drones.values()

    @property
    def inbound_log_queue(self) -> Queue[LogMessage]:
        assert self._inbound_log_message_queue
        return self._inbound_log_message_queue

    @property
    def outbound_pulse_queue(self) -> Queue[Drone]:
        assert self._output_pulse_queue
        return self._output_pulse_queue

    async def initialize_queues(self) -> None:
        self._inbound_log_message_queue = Queue()
        self._output_pulse_queue = Queue()

    def register_drone(self, drone: RegisteredDrone) -> None:
        self.drones[drone.uuid] = drone

    async def register_socket(self, socket: WebSocket) -> None:
        await socket.accept()
        self.pulse_sockets.append(socket)

    async def unregister_socket(self, socket: WebSocket) -> None:
        self.pulse_sockets.remove(socket)
        await socket.close()

    @property
    def argos_drones(self) -> Generator[RegisteredDrone, None, None]:
        return (drone for drone in self.drones.values() if drone.drone_type == DroneType.ARGOS)

    @property
    def crazyflie_drones(self) -> Generator[RegisteredDrone, None, None]:
        return (drone for drone in self.drones.values() if drone.drone_type == DroneType.CRAZYFLIE)


def get_registry() -> Registry:
    @lru_cache(maxsize=None)
    def _get_cached_registry() -> Registry:
        return Registry()

    return _get_cached_registry()
