import asyncio

from backend.tasks.inbound_log_processing_task import process_incoming_logs
from backend.tasks.outbound_drone_pulses_task import process_outbound_drone_pulses


async def initiate_tasks() -> None:
    asyncio.create_task(process_incoming_logs())
    asyncio.create_task(process_outbound_drone_pulses())
