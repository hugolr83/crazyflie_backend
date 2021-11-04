from __future__ import annotations

import json
from asyncio import Queue
from dataclasses import dataclass
from typing import Any, Final, Generator, Type

from cflib.crazyflie.log import LogConfig
from coveo_functools import flex
from fastapi.logger import logger


@dataclass
class LogMessage:
    drone_uuid: str
    timestamp: int


# Since the bandwith with Crazyflie is limited, we need to send the data in multiple packets
@dataclass
class BatteryAndPositionLogMessage(LogMessage):
    kalman_state_x: float
    kalman_state_y: float
    kalman_state_z: float
    pm_vbat: float
    drone_battery_level: int


@dataclass
class RangeLogMessage(LogMessage):
    range_front: int
    range_back: int
    range_up: int
    range_left: int
    range_right: int
    range_zrange: int


# No need to split packets from Argos simulated drones
@dataclass
class FullLogMessage(BatteryAndPositionLogMessage, RangeLogMessage):
    pass


@dataclass
class LogConfigVariable:
    name: str
    fetch_as: str


@dataclass
class LogConfigConfiguration:
    name: str
    period_ms: float
    variables: list[LogConfigVariable]
    dataclass: Type[LogMessage]


CRAZYFLIE_LOG_CONFIG_PERIOD_MS: Final = 800
CRAZYFLIE_LOG_CONFIGS: Final = [
    LogConfigConfiguration(
        "battery_and_position",
        CRAZYFLIE_LOG_CONFIG_PERIOD_MS,
        [
            LogConfigVariable("pm.vbat", "float"),
            LogConfigVariable("drone.batteryLevel", "uint8_t"),
            LogConfigVariable("kalman.stateX", "float"),
            LogConfigVariable("kalman.stateY", "float"),
            LogConfigVariable("kalman.stateZ", "float"),
        ],
        BatteryAndPositionLogMessage,
    ),
    LogConfigConfiguration(
        "range",
        CRAZYFLIE_LOG_CONFIG_PERIOD_MS,
        [
            LogConfigVariable("range.front", "uint16_t"),
            LogConfigVariable("range.back", "uint16_t"),
            LogConfigVariable("range.up", "uint16_t"),
            LogConfigVariable("range.left", "uint16_t"),
            LogConfigVariable("range.right", "uint16_t"),
            LogConfigVariable("range.zrange", "uint16_t"),
        ],
        RangeLogMessage,
    ),
]


def generate_log_configs() -> Generator[LogConfig, None, None]:
    for configuration in CRAZYFLIE_LOG_CONFIGS:
        log_config = LogConfig(configuration.name, configuration.period_ms)
        for variable in configuration.variables:
            log_config.add_variable(variable.name, variable.fetch_as)
        yield log_config


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


async def on_incoming_argos_log_message(drone_uuid: str, inbound_queue: Queue[LogMessage], data: bytes) -> None:
    incoming_data = json.loads(data) | {"drone_uuid": drone_uuid}
    await inbound_queue.put(flex.deserialize(value=incoming_data, hint=FullLogMessage))
