from fastapi import APIRouter

from backend.communication.command import Command
from backend.communication.communication import send_command_to_all_drones
from backend.database.statements import get_mission
from backend.exceptions.response import DroneNotFoundException, WrongDroneTypeException
from backend.models.drone import Drone, DroneType
from backend.registry import get_registry
from backend.routers.utils import generate_responses_documentation

router = APIRouter(prefix="/crazyflie", tags=["crazyflie"])


@router.post(
    "/identify",
    operation_id="identify_crazyflie",
    response_model=Drone,
    responses=generate_responses_documentation(DroneNotFoundException, WrongDroneTypeException),
)
async def identify(drone_id: int) -> Drone:
    """Identify a specific Crazyflie drone. The LEDs of that drone will flash for a couple of seconds."""
    if not (drone := get_registry().get_drone(drone_id)):
        raise DroneNotFoundException(drone_id)

    if drone.drone_type != DroneType.CRAZYFLIE:
        raise WrongDroneTypeException(drone.drone_type)

    await drone.link.send_command(Command.IDENTIFY)
    return drone.to_model()


@router.post(
    "/p2p",
    operation_id="activate_p2p",
    response_model=list[Drone],
    responses=generate_responses_documentation(WrongDroneTypeException),
)
async def p2p(mission_id: int) -> list[Drone]:
    """Identify a specific Crazyflie drone. The LEDs of that drone will flash for a couple of seconds."""
    mission = await get_mission(mission_id)

    if mission.drone_type != DroneType.CRAZYFLIE:
        raise WrongDroneTypeException(mission.drone_type)

    return await send_command_to_all_drones(
        Command.ACTIVATE_P2P, list(get_registry().get_drones(mission.drone_type)), mission_id
    )
