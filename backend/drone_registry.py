import os
import uuid
from asyncio import Queue
from dataclasses import dataclass, field
from functools import lru_cache, partial
from itertools import count, islice
from typing import AsyncGenerator, Final, Generator, Optional

from cflib import crtp
from fastapi.logger import logger

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.crazyflie_drone_link import CrazyflieDroneLink
from backend.registered_drone import RegisteredDrone
from backend.communication.message import Message
from backend.exceptions.communication import ArgosCommunicationException, CrazyflieCommunicationException
from backend.models.drone import DroneType
from backend.utils import get_environment_variable_or_raise

ARGOS_ENDPOINT_ENV_VAR: Final = "ARGOS_ENDPOINT"
ARGOS_DRONES_STARTING_PORT_ENV_VAR: Final = "ARGOS_DRONES_STARTING_PORT"
ARGOS_NUMBER_OF_DRONES_ENV_VAR: Final = "ARGOS_NUMBER_OF_DRONES"
DISABLE_ARGOS_LINKS_ENV_VAR: Final = "DISABLE_ARGOS_LINKS"
DISABLE_CRAZYFLIE_LINKS_ENV_VAR: Final = "DISABLE_CRAZYFLIE_LINKS"


CRAZYFLIE_URIS: Final = ["radio://0/21/2M/E7E7E7E701", "radio://0/21/2M/E7E7E7E702"]


@dataclass
class DroneRegistry:
    drones: dict[str, RegisteredDrone] = field(default_factory=dict)
    inbound_queue: Queue[Message] = Queue()

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
def get_registry() -> DroneRegistry:
    return DroneRegistry()


async def on_incoming_message(drone_uuid: str, data: bytes, inbound_queue: Queue[Message]) -> None:
    await inbound_queue.put(Message(drone_uuid, data))


async def initiate_argos_drones(inbound_queue: Queue[Message]) -> AsyncGenerator[RegisteredDrone, None]:
    argos_endpoint = get_environment_variable_or_raise(ARGOS_ENDPOINT_ENV_VAR)
    argos_drones_staring_port = int(get_environment_variable_or_raise(ARGOS_DRONES_STARTING_PORT_ENV_VAR))
    argos_number_of_drones = int(get_environment_variable_or_raise(ARGOS_NUMBER_OF_DRONES_ENV_VAR))

    for drone_port in islice(count(argos_drones_staring_port), argos_number_of_drones):
        try:
            drone_uuid = str(uuid.uuid4())
            drone_link = await ArgosDroneLink.create(
                argos_endpoint,
                drone_port,
                partial(on_incoming_message, drone_uuid=drone_uuid, inbound_queue=inbound_queue),
            )
            yield RegisteredDrone(drone_uuid, drone_link)
        except ArgosCommunicationException as e:
            logger.warning(f"Unable to connect to Argos drone on port {drone_port}")
            logger.debug(e)


async def initiate_crazyflie_drones(inbound_queue: Queue[Message]) -> AsyncGenerator[RegisteredDrone, None]:
    crtp.init_drivers(enable_debug_driver=False)

    for uri in CRAZYFLIE_URIS:
        try:
            drone_uuid = str(uuid.uuid4())
            drone_link = await CrazyflieDroneLink.create(
                uri, partial(on_incoming_message, drone_uuid=drone_uuid, inbound_queue=inbound_queue)
            )
            yield RegisteredDrone(drone_uuid, drone_link)
        except CrazyflieCommunicationException as e:
            logger.warning(f"Unable to connect to Crazyflie {uri}")
            logger.debug(e)


async def initiate_links() -> None:
    registry = get_registry()

    if not os.getenv(DISABLE_ARGOS_LINKS_ENV_VAR):
        async for drone in initiate_argos_drones(registry.inbound_queue):
            registry.register_drone(drone)
    else:
        logger.warning(f"Not connecting to Argos drones since {DISABLE_ARGOS_LINKS_ENV_VAR} is set")

    if not os.getenv(DISABLE_CRAZYFLIE_LINKS_ENV_VAR):
        async for drone in initiate_crazyflie_drones(registry.inbound_queue):
            registry.register_drone(drone)
    else:
        logger.warning(f"Not connecting to Crazyflie drones since {DISABLE_CRAZYFLIE_LINKS_ENV_VAR} is set")
