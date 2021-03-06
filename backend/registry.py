from asyncio import Queue
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Generator, Optional

from backend.communication.log_message import CrazyflieDebugMessage, LogMessage
from backend.database.models import SavedLog
from backend.models.drone import DroneType
from backend.registered_drone import RegisteredDrone
from backend.tasks.backend_task import BackendTask


@dataclass
class Registry:
    drones: dict[int, RegisteredDrone] = field(default_factory=dict)
    backend_tasks: list[BackendTask] = field(default_factory=list)

    active_argos_mission_id: Optional[int] = None
    active_crazyflie_mission_id: Optional[int] = None

    _crazyflie_debug_queue: Optional[Queue[CrazyflieDebugMessage]] = None
    _inbound_log_message_queue: Optional[Queue[LogMessage]] = None
    _logging_queue: Optional[Queue[SavedLog]] = None
    _mission_termination_queue: Optional[Queue[DroneType]] = None

    def get_drone(self, drone_id: int) -> Optional[RegisteredDrone]:
        return self.drones.get(drone_id)

    def get_drones(self, drone_type: Optional[DroneType]) -> Generator[RegisteredDrone, None, None]:
        if drone_type:
            yield from self.argos_drones if drone_type == DroneType.ARGOS else self.crazyflie_drones
        else:
            yield from self.drones.values()

    @property
    def crazyflie_debug_queue(self) -> Queue[CrazyflieDebugMessage]:
        assert self._crazyflie_debug_queue
        return self._crazyflie_debug_queue

    @property
    def inbound_log_queue(self) -> Queue[LogMessage]:
        assert self._inbound_log_message_queue
        return self._inbound_log_message_queue

    @property
    def logging_queue(self) -> Queue[SavedLog]:
        assert self._logging_queue
        return self._logging_queue

    @property
    def mission_termination_queue(self) -> Queue[DroneType]:
        assert self._mission_termination_queue
        return self._mission_termination_queue

    async def initialize_queues(self) -> None:
        """The lazy initialization is needed to map the Queue to the correct event loop"""
        self._inbound_log_message_queue = Queue()
        self._logging_queue = Queue()
        self._crazyflie_debug_queue = Queue()
        self._mission_termination_queue = Queue()

    def register_drone(self, drone: RegisteredDrone) -> None:
        self.drones[drone.id] = drone

    def unregister_drone(self, drone: RegisteredDrone) -> None:
        if self.drones.get(drone.id):
            del self.drones[drone.id]

    def register_task(self, task: BackendTask) -> None:
        self.backend_tasks.append(task)

    def unregister_task(self, task: BackendTask) -> None:
        self.backend_tasks.remove(task)

    def get_active_mission_id(self, drone_type: DroneType) -> Optional[int]:
        return self.active_argos_mission_id if drone_type == DroneType.ARGOS else self.active_crazyflie_mission_id

    def set_active_mission_id(self, mission_id: int, drone_type: DroneType) -> None:
        if drone_type == DroneType.ARGOS:
            self.active_argos_mission_id = mission_id
        else:
            self.active_crazyflie_mission_id = mission_id

    def clear_active_mission_id(self, drone_type: DroneType) -> None:
        if drone_type == DroneType.ARGOS:
            self.active_argos_mission_id = None
        else:
            self.active_crazyflie_mission_id = None

    @property
    def argos_drones(self) -> Generator[RegisteredDrone, None, None]:
        return (drone for drone in self.drones.values() if drone.drone_type == DroneType.ARGOS)

    @property
    def crazyflie_drones(self) -> Generator[RegisteredDrone, None, None]:
        return (drone for drone in self.drones.values() if drone.drone_type == DroneType.CRAZYFLIE)


@lru_cache(maxsize=None)
def get_registry() -> Registry:
    return Registry()
