import asyncio
import itertools
import uuid
from asyncio import Event
from functools import partial
from itertools import count, islice
from typing import Final

from cflib import crtp
from coveo_settings import IntSetting, StringSetting
from fastapi.logger import logger

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.crazyflie_drone_link import CrazyflieDroneLink
from backend.communication.log_message import on_incoming_crazyflie_log_message
from backend.exceptions.communication import CrazyflieCommunicationException
from backend.registered_drone import RegisteredDrone
from backend.registry import get_registry

ARGOS_ENDPOINT: Final = StringSetting("argos.endpoint", fallback="simulation")
ARGOS_DRONES_STARTING_PORT: Final = IntSetting("argos.starting_port", fallback=3995)
ARGOS_NUMBER_OF_DRONES: Final = IntSetting("argos.number_of_drones", fallback=2)

CRAZYFLIE_ADDRESSES: Final = [0xE7E7E7E701, 0xE7E7E7E702]


async def initiate_argos_drone_link(drone_port: int) -> None:
    drone_uuid = str(uuid.uuid4())
    drone_link = await ArgosDroneLink.create(
        str(ARGOS_ENDPOINT),
        drone_port,
        partial(
            on_incoming_crazyflie_log_message, drone_uuid=drone_uuid, inbound_queue=get_registry().inbound_log_queue
        ),
    )
    get_registry().register_drone(RegisteredDrone(drone_uuid, drone_link, Event(), Event()))


async def initiate_crazyflie_drone_link(crazyflie_address: int) -> None:
    scanned_uris: list[str]
    if not (scanned_uris := list(filter(None, itertools.chain(*crtp.scan_interfaces(crazyflie_address))))):
        raise CrazyflieCommunicationException(hex(crazyflie_address))

    drone_uri: str = next(iter(scanned_uris))
    drone_uuid = str(uuid.uuid4())
    drone_link = await CrazyflieDroneLink.create(
        drone_uri,
        partial(
            on_incoming_crazyflie_log_message, drone_uuid=drone_uuid, inbound_queue=get_registry().inbound_log_queue
        ),
    )
    get_registry().register_drone(RegisteredDrone(drone_uuid, drone_link, Event(), Event()))


async def initiate_links() -> None:
    await get_registry().initialize_queues()

    argos_drones_initiation = (
        initiate_argos_drone_link(drone_port)
        for drone_port in islice(count(int(ARGOS_DRONES_STARTING_PORT)), int(ARGOS_NUMBER_OF_DRONES))
    )

    crtp.init_drivers()
    crazyflie_drones_initiation = (initiate_crazyflie_drone_link(address) for address in CRAZYFLIE_ADDRESSES)

    results = await asyncio.gather(*crazyflie_drones_initiation, *argos_drones_initiation, return_exceptions=True)
    for exception in (result for result in results if isinstance(result, Exception)):
        logger.error(exception)
