import asyncio
import logging

from backend.registry import get_registry
from backend.tasks.backend_task import BackendTask


class InboundLogProcessingTask(BackendTask):
    async def run(self) -> None:
        try:
            registry = get_registry()
            while log_message := await registry.inbound_log_queue.get():
                if not (drone := registry.get_drone(log_message.drone_uuid)):
                    logging.error(
                        f"Received message for drone with UUID {log_message.drone_uuid}, but the drone is unregistered"
                    )
                    continue

                drone.update_from_log_message(log_message)
                if drone.should_process_updated_telemetry():
                    await registry.outbound_pulse_queue.put(drone.to_model())
        except asyncio.CancelledError:
            pass