import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket

from backend.communication.command import Command
from backend.models.drone import Drone, DroneType
from backend.registered_drone import RegisteredDrone
from backend.registry import get_registry

router = APIRouter(tags=["common"])


async def send_command_to_all_drones(command: Command, all_drones: list[RegisteredDrone]) -> list[Drone]:
    # TODO: Handle exception
    await asyncio.gather(*(drone.link.send_command(command) for drone in all_drones))

    return [drone.to_model() for drone in all_drones]


@router.get("/drones", operation_id="get_drones", response_model=list[Drone])
async def drones(drone_type: Optional[DroneType] = None) -> list[Drone]:
    """Retrieve all the currently registered drones. You can also filter which type of drone you want."""
    return list(map(lambda drone: drone.to_model(), get_registry().get_drones(drone_type)))


@router.post("/start_mission", operation_id="start_mission", response_model=list[Drone])
async def start_exploration(drone_type: DroneType) -> list[Drone]:
    """Start the mission for a specific drone type. Will communicate with all registered drones of that type."""
    return await send_command_to_all_drones(Command.START_EXPLORATION, list(get_registry().get_drones(drone_type)))


@router.post("/end_mission", operation_id="end_mission", response_model=list[Drone])
async def end_mission(drone_type: DroneType) -> list[Drone]:
    """End the mission (immediate landing) for a specific drone type. Will communicate with all registered drones of
    that type.
    """
    return await send_command_to_all_drones(Command.LAND, list(get_registry().get_drones(drone_type)))


@router.post("/return_to_base", operation_id="return_to_base", response_model=list[Drone])
async def return_to_base(drone_type: DroneType) -> list[Drone]:
    """Return to base for a specific drone type. Will communicate with all registered drones of that type."""
    return await send_command_to_all_drones(Command.RETURN_TO_BASE, list(get_registry().get_drones(drone_type)))


@router.websocket("/drone_pulses")
async def drone_pulses(websocket: WebSocket) -> None:
    """Start a WebSocket that subscribe to drone state updates"""
    await get_registry().register_socket(websocket)
