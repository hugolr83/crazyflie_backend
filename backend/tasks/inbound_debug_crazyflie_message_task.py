import asyncio

from fastapi.logger import logger

from backend.database.models import SavedLog
from backend.database.statements import insert_log_in_database
from backend.registry import get_registry
from backend.tasks.backend_task import BackendTask


class InboundDebugCrazyflieMessageTask(BackendTask):
    async def run(self) -> None:
        try:
            registry = get_registry()
            while crazyflie_debug_message := await registry.crazyflie_debug_queue.get():
                if not (drone := registry.get_drone(crazyflie_debug_message.drone_uuid)):
                    logger.error(f"Drone with uuid {crazyflie_debug_message.drone_uuid} isn't found")

                if mission_id := drone.active_mission_id:  # type: ignore[union-attr]
                    await registry.logging_queue.put(
                        SavedLog(
                            mission_id=mission_id,
                            timestamp=crazyflie_debug_message.timestamp,
                            message=crazyflie_debug_message.message,
                        )
                    )
        except asyncio.CancelledError:
            pass
