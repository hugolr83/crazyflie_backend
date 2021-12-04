import asyncio
import json
from asyncio import Queue
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from cflib.crazyflie.log import LogTocElement, LogVariable

from backend.communication.log_message import (
    BatteryAndPositionLogMessage,
    CRAZYFLIE_LOG_CONFIGS,
    FullLogMessage,
    LogMessage,
    RangeLogMessage,
    generate_log_configs,
    on_incoming_argos_log_message,
    on_incoming_crazyflie_log_message,
)

# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


def test_generate_log_configs() -> None:
    for log_config in generate_log_configs():
        configuration = next((config for config in CRAZYFLIE_LOG_CONFIGS if config.name == log_config.name))
        assert int(configuration.period_ms / 10) == log_config.period  # yeah, ask Bitcraze for that shit
        assert len(configuration.variables) == len(log_config.variables)
        for variable in configuration.variables:
            matched_var: LogVariable = next(
                (
                    crazyflie_variable
                    for crazyflie_variable in log_config.variables
                    if crazyflie_variable.name == variable.name
                )
            )
            assert matched_var.fetch_as == LogTocElement.get_id_from_cstring(variable.fetch_as)


async def test_crazyflie_message_are_queued_on_incoming_battery_message() -> None:
    queue: Queue[LogMessage] = Queue()
    log_message = BatteryAndPositionLogMessage(
        drone_id=1,
        timestamp=123,
        kalman_state_x=1,
        kalman_state_y=2,
        kalman_state_z=3,
        state_estimate_yaw=40,
        drone_state=0,
        drone_battery_level=10,
    )
    data: dict[str, Any] = {
        "drone.state": log_message.drone_state,
        "drone.batteryLevel": log_message.drone_battery_level,
        "kalman.stateX": log_message.kalman_state_x,
        "kalman.stateY": log_message.kalman_state_y,
        "kalman.stateZ": log_message.kalman_state_z,
        "state_estimate_yaw": log_message.state_estimate_yaw,
    }
    log_config = next(config for config in generate_log_configs() if config.name == "battery_and_position")

    await on_incoming_crazyflie_log_message(
        log_message.drone_id, queue, log_message.timestamp, data=data, log_config=log_config
    )

    message = await asyncio.wait_for(queue.get(), 0.1)
    assert message == log_message


async def test_crazyflie_messages_are_queued_on_incoming_range_message() -> None:
    queue: Queue[LogMessage] = Queue()
    log_message = RangeLogMessage(
        drone_id=1,
        timestamp=123,
        range_front=10,
        range_back=11,
        range_up=13,
        range_zrange=43,
        range_left=112,
        range_right=1031,
    )
    data: dict[str, Any] = {
        "range.front": log_message.range_front,
        "range.back": log_message.range_back,
        "range.up": log_message.range_up,
        "range.zrange": log_message.range_zrange,
        "range.left": log_message.range_left,
        "range.right": log_message.range_right,
    }
    log_config = next(config for config in generate_log_configs() if config.name == "range")

    await on_incoming_crazyflie_log_message(
        log_message.drone_id, queue, log_message.timestamp, data=data, log_config=log_config
    )

    message = await asyncio.wait_for(queue.get(), 0.1)
    assert message == log_message


@patch("backend.communication.log_message.logger")
async def test_errors_are_logged_on_unsupported_config_name(logger_mock: MagicMock) -> None:
    log_config = next(generate_log_configs())
    log_config.name = "bAdNaMe"

    await on_incoming_crazyflie_log_message(1, Queue(), 0, {}, log_config)

    logger_mock.error.assert_called()


async def test_argos_messages_are_queued_on_incoming_message() -> None:
    queue: Queue[LogMessage] = Queue()
    log_message = FullLogMessage(
        drone_id=1,
        timestamp=123,
        kalman_state_x=1,
        kalman_state_y=2,
        kalman_state_z=3,
        state_estimate_yaw=40,
        drone_state=0,
        drone_battery_level=10,
        range_front=10,
        range_back=11,
        range_up=13,
        range_zrange=43,
        range_left=112,
        range_right=1031,
    )
    data: dict[str, Any] = {
        "timestamp": log_message.timestamp,
        "drone.state": log_message.drone_state,
        "drone.batteryLevel": log_message.drone_battery_level,
        "kalman.stateX": log_message.kalman_state_x,
        "kalman.stateY": log_message.kalman_state_y,
        "kalman.stateZ": log_message.kalman_state_z,
        "state_estimate_yaw": log_message.state_estimate_yaw,
        "range.front": log_message.range_front,
        "range.back": log_message.range_back,
        "range.up": log_message.range_up,
        "range.zrange": log_message.range_zrange,
        "range.left": log_message.range_left,
        "range.right": log_message.range_right,
    }

    await on_incoming_argos_log_message(log_message.drone_id, queue, json.dumps(data).encode("utf-8"))

    message = await asyncio.wait_for(queue.get(), 0.1)
    assert message == log_message
