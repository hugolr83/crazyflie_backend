from asyncio import Queue
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Generator, Optional

from starlette.websockets import WebSocket

from backend.communication.log_message import LogMessage
from backend.models.drone import DroneType
from backend.registered_drone import RegisteredDrone
from backend.tasks.backend_task import BackendTask


@dataclass
class Registry:
    drones: dict[str, RegisteredDrone] = field(default_factory=dict)
    backend_tasks: list[BackendTask] = field(default_factory=list)
    _inbound_log_message_queue: Optional[Queue[LogMessage]] = None

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

    async def initialize_queues(self) -> None:
        self._inbound_log_message_queue = Queue()

    def register_drone(self, drone: RegisteredDrone) -> None:
        self.drones[drone.uuid] = drone

    def unregister_drone(self, drone: RegisteredDrone) -> None:
        if self.drones.get(drone.uuid):
            del self.drones[drone.uuid]

    def register_task(self, task: BackendTask) -> None:
        self.backend_tasks.append(task)

    def unregister_task(self, task: BackendTask) -> None:
        self.backend_tasks.remove(task)

    @property
    def argos_drones(self) -> Generator[RegisteredDrone, None, None]:
        return (drone for drone in self.drones.values() if drone.drone_type == DroneType.ARGOS)

    @property
    def crazyflie_drones(self) -> Generator[RegisteredDrone, None, None]:
        return (drone for drone in self.drones.values() if drone.drone_type == DroneType.CRAZYFLIE)


@lru_cache(maxsize=None)
def get_registry() -> Registry:
    return Registry()
