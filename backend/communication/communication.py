import asyncio

from backend.communication.command import Command
from backend.models.drone import Drone
from backend.registered_drone import RegisteredDrone


async def send_command_to_all_drones(command: Command, all_drones: list[RegisteredDrone]) -> list[Drone]:
    # TODO: Handle exception
    await asyncio.gather(*(drone.link.send_command(command) for drone in all_drones))

    return [drone.to_model() for drone in all_drones]
