from fastapi import APIRouter

from backend.communication.command import Command
from backend.drone_registry import get_registry
from backend.exceptions.response import DroneNotFoundException, WrongDroneTypeException
from backend.models.drone_model import DroneModel, DroneType
from backend.utils import generate_responses_documentation

router = APIRouter(prefix="/crazyflie", tags=["crazyflie"])


@router.post(
    "/identify",
    response_model=DroneModel,
    responses=generate_responses_documentation(DroneNotFoundException, WrongDroneTypeException),
)
async def identify(uuid: str) -> DroneModel:
    if not (drone := get_registry().get_drone(uuid)):
        raise DroneNotFoundException(uuid)

    if drone.drone_type != DroneType.CRAZYFLIE:
        raise WrongDroneTypeException(drone.drone_type)

    await drone.link.send_command(Command.IDENTIFY)
    return drone.to_model()
