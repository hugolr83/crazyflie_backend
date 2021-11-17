from __future__ import annotations

import datetime
import json
from asyncio import Queue
from typing import Any

from cflib.crazyflie.log import LogConfig
from coveo_functools import flex
from fastapi.logger import logger

from backend.communication.messages import CRAZYFLIE_LOG_CONFIGS, CrazyflieDebugMessage, FullLogMessage, LogMessage


async def on_incoming_crazyflie_log_message(
    drone_uuid: str, inbound_queue: Queue[LogMessage], timestamp: int, data: dict[str, Any], log_config: LogConfig
) -> None:
    log_message_type = next(
        (config.dataclass for config in CRAZYFLIE_LOG_CONFIGS if log_config.name == config.name), None
    )

    if log_message_type:
        incoming_data = data | {"drone_uuid": drone_uuid, "timestamp": timestamp}
        await inbound_queue.put(flex.deserialize(value=incoming_data, hint=log_message_type))
    else:
        logger.error(f"LogConfig with name {log_config.name} is unknown")


async def on_incoming_crazyflie_debug_message(
    message: str, drone_uuid: str, crazyflie_debug_queue: Queue[CrazyflieDebugMessage]
) -> None:
    await crazyflie_debug_queue.put(
        CrazyflieDebugMessage(drone_uuid=drone_uuid, timestamp=datetime.datetime.now(), message=message)
    )


async def on_incoming_argos_log_message(drone_uuid: str, inbound_queue: Queue[LogMessage], data: bytes) -> None:
    incoming_data = json.loads(data) | {"drone_uuid": drone_uuid}
    await inbound_queue.put(flex.deserialize(value=incoming_data, hint=FullLogMessage))
