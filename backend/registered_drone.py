from dataclasses import dataclass
from functools import singledispatchmethod

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.drone_link import DroneLink
from backend.communication.log_message import (
    BatteryAndPositionLogMessage,
    FullLogMessage,
    LogMessage,
    RangeLogMessage,
    STATES,
)
from backend.models.drone import Drone, DroneBattery, DroneRange, DroneState, DroneType, DroneVec3, Orientation


@dataclass
class RegisteredDrone:
    uuid: str
    link: DroneLink
    state: DroneState = DroneState.NOT_READY
    battery: DroneBattery = DroneBattery(charge_percentage=0, voltage=0.0)
    position: DroneVec3 = DroneVec3(x=0.0, y=0.0, z=0.0)
    orientation: Orientation = Orientation(yaw=0.0)
    range: DroneRange = DroneRange(front=0.0, back=0.0, up=0.0, left=0.0, right=0.0, bottom=0.0)

    @property
    def drone_type(self) -> DroneType:
        return DroneType.ARGOS if isinstance(self.link, ArgosDroneLink) else DroneType.CRAZYFLIE

    @singledispatchmethod
    def update_from_log_message(self, log_message: LogMessage) -> None:
        raise NotImplementedError("log_message must be an instance of a child class of LogMessage")  # pragma: no cover

    @update_from_log_message.register
    def _update_battery_and_position(self, log_message: BatteryAndPositionLogMessage) -> None:
        self.battery = DroneBattery(charge_percentage=log_message.drone_battery_level)
        self.position = DroneVec3(
            x=log_message.kalman_state_x, y=log_message.kalman_state_y, z=log_message.kalman_state_z
        )
        self.orientation = Orientation(yaw=log_message.state_estimate_yaw)
        self.state = STATES[log_message.drone_state]

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

    @update_from_log_message.register
    def _update_all_field(self, log_message: FullLogMessage) -> None:
        self._update_battery_and_position(log_message)
        self._update_range(log_message)

    def to_model(self) -> Drone:
        return Drone(
            uuid=self.uuid,
            state=self.state,
            type=self.drone_type,
            battery=self.battery,
            position=self.position,
            orientation=self.orientation,
            range=self.range,
        )
