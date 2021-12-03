import asyncio
import logging

from backend.database.statements import end_mission, get_mission
from backend.models.mission import Mission, MissionState
from backend.registry import get_registry
from backend.tasks.backend_task import BackendTask


async def process_end_mission(mission: Mission) -> None:
    total_distance = sum((drone.total_distance for drone in get_registry().get_drones(mission.drone_type)))
    await end_mission(mission.id, total_distance)


class ProcessMissionTerminationTask(BackendTask):
    async def run(self) -> None:
        try:
            registry = get_registry()
            while drone_type := await registry.mission_termination_queue.get():
                active_mission = registry.get_active_mission_id(drone_type)
                if not active_mission:
                    continue

                if any((drone.is_flying for drone in registry.get_drones(drone_type))):
                    continue

                mission = await get_mission(active_mission)
                if mission.state in (MissionState.PENDING_ENDED, MissionState.RETURNED_TO_BASE):
                    await process_end_mission(mission)
                    registry.clear_active_mission_id(mission.drone_type)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(e)
