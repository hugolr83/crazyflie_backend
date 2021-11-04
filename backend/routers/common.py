from typing import Optional

from fastapi import APIRouter

from backend.communication.command import Command
from backend.communication.communication import send_command_to_all_drones
from backend.database.statements import create_new_mission, get_log_message, start_existing_mission
from backend.models.drone import Drone, DroneType
from backend.models.mission import Log, Mission
from backend.registry import get_registry

router = APIRouter(tags=["common"])


@router.get("/drones", operation_id="get_drones", response_model=list[Drone])
async def drones(drone_type: Optional[DroneType] = None) -> list[Drone]:
    """Retrieve all the currently registered drones. You can also filter which type of drone you want."""
    return list(map(lambda drone: drone.to_model(), get_registry().get_drones(drone_type)))


@router.get("/logs", operation_id="get_logs", response_model=list[Log])
async def get_logs(starting_id: int = 0) -> list[Log]:
    return await get_log_message(starting_id)


@router.post("/mission", operation_id="create_mission", response_model=Mission)
async def create_mission(drone_type: DroneType) -> Mission:
    """Create a new mission"""
    return await create_new_mission(drone_type)


@router.post("/start_mission", operation_id="start_mission", response_model=list[Drone])
async def start_mission(drone_type: DroneType, mission_id: int) -> list[Drone]:
    """Start the mission for a specific drone type. Will communicate with all registered drones of that type."""
    await start_existing_mission(mission_id)
    selected_drones = list(get_registry().get_drones(drone_type))
    for drone in selected_drones:
        drone.active_mission_id = mission_id
    return await send_command_to_all_drones(Command.START_EXPLORATION, selected_drones, mission_id)


@router.post("/end_mission", operation_id="end_mission", response_model=list[Drone])
async def end_mission(drone_type: DroneType, mission_id: int) -> list[Drone]:
    """End the mission (immediate landing) for a specific drone type. Will communicate with all registered drones of
    that type.
    """
    return await send_command_to_all_drones(Command.LAND, list(get_registry().get_drones(drone_type)), mission_id)


@router.post("/return_to_base", operation_id="return_to_base", response_model=list[Drone])
async def return_to_base(drone_type: DroneType, mission_id: int) -> list[Drone]:
    """Return to base for a specific drone type. Will communicate with all registered drones of that type."""
    return await send_command_to_all_drones(
        Command.RETURN_TO_BASE, list(get_registry().get_drones(drone_type)), mission_id
    )
