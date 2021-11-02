from unittest.mock import MagicMock

from backend.communication.drone_link import DroneLink
from backend.communication.log_message import BatteryAndPositionLogMessage, FullLogMessage, RangeLogMessage
from backend.models.drone import DroneBattery, DroneRange, DroneVec3
from backend.registered_drone import RegisteredDrone


def test_update_from_battery_and_position_log_message() -> None:
    registered_drone = RegisteredDrone("uuid", MagicMock(spec=DroneLink))
    log_message = BatteryAndPositionLogMessage(
        drone_uuid="uuid",
        timestamp=2,
        kalman_state_x=10,
        kalman_state_y=11,
        kalman_state_z=12,
        pm_vbat=3.8,
        drone_battery_level=90,
    )

    registered_drone.update_from_log_message(log_message)

    assert registered_drone.battery == DroneBattery(charge_percentage=90, voltage=3.8)
    assert registered_drone.position == DroneVec3(x=10, y=11, z=12)


def test_update_from_range_log_message() -> None:
    registered_drone = RegisteredDrone("uuid", MagicMock(spec=DroneLink))
    log_message = RangeLogMessage(
        drone_uuid="uuid",
        timestamp=2,
        range_front=110,
        range_back=111,
        range_up=112,
        range_zrange=113,
        range_left=114,
        range_right=116,
    )

    registered_drone.update_from_log_message(log_message)

    assert registered_drone.range == DroneRange(
        front=log_message.range_front,
        back=log_message.range_back,
        up=log_message.range_up,
        left=log_message.range_left,
        right=log_message.range_right,
        bottom=log_message.range_zrange,
    )


def test_update_from_full_message() -> None:
    registered_drone = RegisteredDrone("uuid", MagicMock(spec=DroneLink))
    log_message = FullLogMessage(
        drone_uuid="uuid",
        timestamp=2,
        kalman_state_x=10,
        kalman_state_y=11,
        kalman_state_z=12,
        pm_vbat=3.8,
        drone_battery_level=90,
        range_front=110,
        range_back=111,
        range_up=112,
        range_zrange=113,
        range_left=114,
        range_right=116,
    )

    registered_drone.update_from_log_message(log_message)

    assert registered_drone.battery == DroneBattery(charge_percentage=90, voltage=3.8)
    assert registered_drone.position == DroneVec3(x=10, y=11, z=12)
    assert registered_drone.range == DroneRange(
        front=log_message.range_front,
        back=log_message.range_back,
        up=log_message.range_up,
        left=log_message.range_left,
        right=log_message.range_right,
        bottom=log_message.range_zrange,
    )
