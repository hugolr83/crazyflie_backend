import asyncio
import logging

from backend.database.statements import insert_log_in_database
from backend.registry import get_registry
from backend.tasks.backend_task import BackendTask


class InsertLogTask(BackendTask):
    async def run(self) -> None:
        try:
            registry = get_registry()
            while log_to_commit := await registry.logging_queue.get():
                logging.warning(f"received message: {log_to_commit}")
                await insert_log_in_database(log_to_commit)
        except asyncio.CancelledError:
            pass
