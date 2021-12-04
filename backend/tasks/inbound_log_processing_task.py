import asyncio
import dataclasses
import datetime
import logging

from fastapi.logger import logger

from backend.database.models import SavedLog
from backend.database.statements import create_drone_metrics
from backend.registry import get_registry
from backend.tasks.backend_task import BackendTask


class InboundLogProcessingTask(BackendTask):
    async def run(self) -> None:
        try:
            registry = get_registry()
            while log_message := await registry.inbound_log_queue.get():
                if not (drone := registry.get_drone(log_message.drone_id)):
                    logger.error(
                        f"Received message for drone with id {log_message.drone_id}, but the drone is unregistered"
                    )
                    continue

                drone.update_from_log_message(log_message)
                if mission_id := registry.get_active_mission_id(drone.drone_type):
                    await create_drone_metrics(drone, mission_id)

                if not drone.is_flying:
                    await registry.mission_termination_queue.put(drone.drone_type)

                if mission_id := drone.active_mission_id:
                    message = "Message received: " + ",".join(
                        f"'{key}': {value}" for key, value in dataclasses.asdict(log_message).items()
                    )
                    await registry.logging_queue.put(
                        SavedLog(mission_id=mission_id, timestamp=datetime.datetime.utcnow(), message=message)
                    )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(e)
