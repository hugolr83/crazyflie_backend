from fastapi import APIRouter

from backend.communication.command import Command
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
