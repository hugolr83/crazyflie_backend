from typing import Final

from backend.registry import get_registry
from backend.tasks.inbound_debug_crazyflie_message_task import InboundDebugCrazyflieMessageTask
from backend.tasks.inbound_log_processing_task import InboundLogProcessingTask
from backend.tasks.insert_log_task import InsertLogTask
from backend.tasks.process_mission_termination_task import ProcessMissionTerminationTask

TASKS_TO_INITIALIZE: Final = [
    InboundLogProcessingTask,
    InboundDebugCrazyflieMessageTask,
    InsertLogTask,
    ProcessMissionTerminationTask,
]


async def initiate_tasks() -> None:
    registry = get_registry()
    for task_constructor in TASKS_TO_INITIALIZE:
        task = task_constructor()  # type: ignore[abstract]
        await task.initiate()
        registry.register_task(task)


async def terminate_tasks() -> None:
    registry = get_registry()
    for task in registry.backend_tasks:
        await task.terminate()
    registry.backend_tasks.clear()
