import asyncio
import datetime
import itertools
import uuid
from functools import partial
from itertools import count, islice
from typing import Final

from cflib import crtp
from coveo_settings import IntSetting, StringSetting
from fastapi.logger import logger

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.command import Command
from backend.communication.crazyflie_drone_link import CrazyflieDroneLink
from backend.communication.log_message import (
    on_incoming_argos_log_message,
    on_incoming_crazyflie_debug_message,
    on_incoming_crazyflie_log_message,
)
from backend.database.models import SavedLog
from backend.database.statements import create_drone
from backend.exceptions.communication import CrazyflieCommunicationException
from backend.models.drone import Drone
from backend.registered_drone import RegisteredDrone
from backend.registry import get_registry

ARGOS_ENDPOINT: Final = StringSetting("argos.endpoint", fallback="localhost")
ARGOS_DRONES_STARTING_PORT: Final = IntSetting("argos.starting_port", fallback=3995)
ARGOS_NUMBER_OF_DRONES: Final = IntSetting("argos.number_of_drones", fallback=2)

CRAZYFLIE_ADDRESSES: Final = [0xE7E7E7EE01, 0xE7E7E7EE02]

next_available_id = 0


def get_next_available_drone_id() -> int:
    global next_available_id
    drone_id = next_available_id
    next_available_id += 1
    return drone_id


async def send_command_to_all_drones(
    command: Command, all_drones: list[RegisteredDrone], mission_id: int
) -> list[Drone]:
    await asyncio.gather(*(drone.link.send_command(command) for drone in all_drones))

    await get_registry().logging_queue.put(
        SavedLog(
            mission_id=mission_id,
            timestamp=datetime.datetime.utcnow(),
            message=f"Sending command {command.name} to drones {', '.join(str(drone.id) for drone in all_drones)}",
        )
    )

    return [drone.to_model() for drone in all_drones]


async def initiate_argos_drone_link(drone_port: int) -> None:
    drone_id = get_next_available_drone_id()
    drone_link = await ArgosDroneLink.create(
        str(ARGOS_ENDPOINT),
        drone_port,
        partial(on_incoming_argos_log_message, drone_id=drone_id, inbound_queue=get_registry().inbound_log_queue),
    )

    drone = RegisteredDrone(drone_id, drone_link)
    await create_drone(drone)
    get_registry().register_drone(drone)


async def initiate_crazyflie_drone_link(crazyflie_address: int) -> None:
    # scan_interfaces returns a list of lists (ಠ_ಠ) so this flatten the result
    scanned_uris: list[str] = list(filter(None, itertools.chain(*crtp.scan_interfaces(crazyflie_address))))
    if not scanned_uris:
        raise CrazyflieCommunicationException(hex(crazyflie_address))

    drone_uri: str = next(iter(scanned_uris))
    drone_id = get_next_available_drone_id()
    drone_link = await CrazyflieDroneLink.create(
        drone_uri,
        partial(on_incoming_crazyflie_log_message, drone_id=drone_id, inbound_queue=get_registry().inbound_log_queue),
        partial(
            on_incoming_crazyflie_debug_message,
            drone_id=drone_id,
            crazyflie_debug_queue=get_registry().crazyflie_debug_queue,
        ),
    )

    drone = RegisteredDrone(drone_id, drone_link)
    await create_drone(drone)
    get_registry().register_drone(drone)


async def initiate_links() -> None:
    await get_registry().initialize_queues()

    crtp.init_drivers()
    for address in CRAZYFLIE_ADDRESSES:
        try:
            await initiate_crazyflie_drone_link(address)
        except CrazyflieCommunicationException as e:
            logger.error(e)

    argos_drones_initiation = (
        initiate_argos_drone_link(drone_port)
        for drone_port in islice(count(int(ARGOS_DRONES_STARTING_PORT)), int(ARGOS_NUMBER_OF_DRONES))
    )

    argos_initiation_results = await asyncio.gather(*argos_drones_initiation, return_exceptions=True)
    for exception in (result for result in argos_initiation_results if isinstance(result, Exception)):
        logger.error(exception)


async def terminate_links() -> None:
    for drone in get_registry().drones.values():
        await drone.link.terminate()
