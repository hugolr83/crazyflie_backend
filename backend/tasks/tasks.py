from typing import Final

from backend.registry import get_registry
from backend.tasks.inbound_log_processing_task import InboundLogProcessingTask
from backend.tasks.outbound_drone_pulses_task import OutboundDronePulsesTask

TASKS_TO_INITIALIZE: Final = [InboundLogProcessingTask, OutboundDronePulsesTask]


async def initiate_tasks() -> None:
    registry = get_registry()
    for task_constructor in TASKS_TO_INITIALIZE:
        task = task_constructor()
        await task.initiate()
        registry.register_task(task)


async def terminate_tasks() -> None:
    registry = get_registry()
    for task in registry.backend_tasks:
        await task.terminate()
