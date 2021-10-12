from asyncio import Event
from dataclasses import dataclass
from functools import singledispatchmethod

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.drone_link import DroneLink
from backend.communication.log_message import (
    BatteryAndPositionLogMessage,
    CompleteLogMessage,
    LogMessage,
    RangeLogMessage,
)
from backend.models.drone import Drone, DroneBattery, DroneRange, DroneType, DroneVec3
from backend.state import DroneState


@dataclass
class RegisteredDrone:
    uuid: str
    link: DroneLink
    battery_and_position_updated: Event
    range_updated: Event
    state: DroneState = DroneState.WAITING
    battery: DroneBattery = DroneBattery(charge_percentage=0, voltage=0.0)
    position: DroneVec3 = DroneVec3(x=0.0, y=0.0, z=0.0)
    range: DroneRange = DroneRange(front=0.0, back=0.0, up=0.0, left=0.0, right=0.0, bottom=0.0)

    @property
    def drone_type(self) -> DroneType:
        return DroneType.ARGOS if isinstance(self.link, ArgosDroneLink) else DroneType.CRAZYFLIE

    @singledispatchmethod
    def update_from_log_message(self, log_message: LogMessage) -> None:
        raise NotImplementedError("log_message must be an instance of a child class of LogMessage")

    @update_from_log_message.register
    def _update_battery_and_position(self, log_message: BatteryAndPositionLogMessage) -> None:
        self.battery = DroneBattery(charge_percentage=log_message.pm_battery_level, voltage=log_message.pm_vbat)
        self.position = DroneVec3(
            x=log_message.kalman_state_x, y=log_message.kalman_state_y, z=log_message.kalman_state_z
        )
        self.battery_and_position_updated.set()

    @update_from_log_message.register
    def _update_range(self, log_message: RangeLogMessage) -> None:
        self.range = DroneRange(
            front=log_message.range_front,
            back=log_message.range_back,
            up=log_message.range_up,
            left=log_message.range_left,
            right=log_message.range_right,
            bottom=log_message.range_zrange,
        )
        self.range_updated.set()

    @update_from_log_message.register
    def _update_all_field(self, log_message: CompleteLogMessage) -> None:
        self._update_battery_and_position(log_message)
        self._update_range(log_message)

    def should_process_updated_telemetry(self) -> bool:
        """Only communicate updated telemetry data once every fields are updated"""
        if self.battery_and_position_updated.is_set() and self.range_updated.is_set():
            self.battery_and_position_updated.clear()
            self.range_updated.clear()
            return True
        return False

    def to_model(self) -> Drone:
        return Drone(
            uuid=self.uuid,
            state=self.state,
            type=self.drone_type,
            battery=self.battery,
            position=self.position,
            range=self.range,
        )
