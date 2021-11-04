import asyncio
import dataclasses
import datetime

from fastapi.logger import logger

from backend.database.models import SavedLog
from backend.registry import get_registry
from backend.tasks.backend_task import BackendTask


class InboundLogProcessingTask(BackendTask):
    async def run(self) -> None:
        try:
            registry = get_registry()
            while log_message := await registry.inbound_log_queue.get():
                if not (drone := registry.get_drone(log_message.drone_uuid)):
                    logger.error(
                        f"Received message for drone with UUID {log_message.drone_uuid}, but the drone is unregistered"
                    )
                    continue

                drone.update_from_log_message(log_message)

                if mission_id := drone.active_mission_id:
                    logger.warning(f"mission_id: {mission_id}")
                    await registry.logging_queue.put(
                        SavedLog(
                            mission_id=mission_id,
                            timestamp=datetime.datetime.now(),
                            message="Message received: "
                            + ",".join(f"'{key}': {value}" for key, value in dataclasses.asdict(log_message).values()),
                        )
                    )
        except asyncio.CancelledError:
            pass
