import datetime
from dataclasses import dataclass
from typing import Final, Generator, Type

from cflib.crazyflie.log import LogConfig

from backend.models.drone import DroneState

DRONE_STATES: Final = {
    0: DroneState.NOT_READY,
    1: DroneState.READY,
    2: DroneState.TAKING_OFF,
    3: DroneState.LANDING,
    4: DroneState.HOVERING,
    5: DroneState.EXPLORING,
    6: DroneState.RETURNING_BASE,
    7: DroneState.CRASHED,
}


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
    state_estimate_yaw: float
    drone_state: int
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
class CrazyflieDebugMessage:
    drone_uuid: str
    timestamp: datetime.datetime
    message: str


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
            LogConfigVariable("drone.state", "uint8_t"),
            LogConfigVariable("drone.batteryLevel", "uint8_t"),
            LogConfigVariable("kalman.stateX", "float"),
            LogConfigVariable("kalman.stateY", "float"),
            LogConfigVariable("kalman.stateZ", "float"),
            LogConfigVariable("stateEstimate.yaw", "float"),
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
