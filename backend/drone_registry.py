import asyncio
import itertools
import uuid
from asyncio import Queue
from dataclasses import dataclass, field
from functools import lru_cache, partial
from itertools import count, islice
from typing import Final, Generator, Optional

from cflib import crtp
from coveo_settings import IntSetting, StringSetting
from fastapi.logger import logger

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.crazyflie_drone_link import CrazyflieDroneLink
from backend.communication.message import Message
from backend.exceptions.communication import CrazyflieCommunicationException
from backend.models.drone import DroneType
from backend.registered_drone import RegisteredDrone

ARGOS_ENDPOINT: Final = StringSetting("argos.endpoint", fallback="simulation")
ARGOS_DRONES_STARTING_PORT: Final = IntSetting("argos.starting_port", fallback=3995)
ARGOS_NUMBER_OF_DRONES: Final = IntSetting("argos.number_of_drones", fallback=2)

CRAZYFLIE_ADDRESSES: Final = [0xE7E7E7E701, 0xE7E7E7E702]


async def on_incoming_message(drone_uuid: str, data: bytes, inbound_queue: Queue[Message]) -> None:
    await inbound_queue.put(Message(drone_uuid, data))


@dataclass
class Registry:
    drones: dict[str, RegisteredDrone] = field(default_factory=dict)
    inbound_queue: Queue[Message] = Queue()

    async def initiate(self) -> None:
        argos_drones_initiation = (
            self.initiate_argos_drone_link(drone_port)
            for drone_port in islice(count(int(ARGOS_DRONES_STARTING_PORT)), int(ARGOS_NUMBER_OF_DRONES))
        )

        crtp.init_drivers()
        crazyflie_drones_initiation = (self.initiate_crazyflie_drone_link(address) for address in CRAZYFLIE_ADDRESSES)

        results = await asyncio.gather(*crazyflie_drones_initiation, *argos_drones_initiation, return_exceptions=True)
        for exception in (result for result in results if isinstance(result, Exception)):
            logger.error(exception)

    async def initiate_argos_drone_link(self, drone_port: int) -> None:
        drone_uuid = str(uuid.uuid4())
        drone_link = await ArgosDroneLink.create(
            str(ARGOS_ENDPOINT),
            drone_port,
            partial(on_incoming_message, drone_uuid=drone_uuid, inbound_queue=self.inbound_queue),
        )
        self.register_drone(RegisteredDrone(drone_uuid, drone_link))

    async def initiate_crazyflie_drone_link(self, crazyflie_address: int) -> None:
        scanned_uris: list[str]
        if not (scanned_uris := list(filter(None, itertools.chain(*crtp.scan_interfaces(crazyflie_address))))):
            raise CrazyflieCommunicationException(hex(crazyflie_address))

        drone_uri: str = next(iter(scanned_uris))
        drone_uuid = str(uuid.uuid4())
        drone_link = await CrazyflieDroneLink.create(
            drone_uri, partial(on_incoming_message, drone_uuid=drone_uuid, inbound_queue=self.inbound_queue)
        )
        self.register_drone(RegisteredDrone(drone_uuid, drone_link))

    def get_drone(self, drone_uuid: str) -> Optional[RegisteredDrone]:
        return self.drones.get(drone_uuid)

    def get_drones(self, drone_type: Optional[DroneType]) -> Generator[RegisteredDrone, None, None]:
        if drone_type:
            yield from self.argos_drones if drone_type == DroneType.ARGOS else self.crazyflie_drones
        else:
            yield from self.drones.values()

    def register_drone(self, drone: RegisteredDrone) -> None:
        self.drones[drone.uuid] = drone

    @property
    def argos_drones(self) -> Generator[RegisteredDrone, None, None]:
        return (drone for drone in self.drones.values() if drone.drone_type == DroneType.ARGOS)

    @property
    def crazyflie_drones(self) -> Generator[RegisteredDrone, None, None]:
        return (drone for drone in self.drones.values() if drone.drone_type == DroneType.CRAZYFLIE)


@lru_cache(maxsize=None)
def get_registry() -> Registry:
    return Registry()
