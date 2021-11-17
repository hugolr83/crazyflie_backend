from enum import Enum

from pydantic import BaseModel


class DroneState(str, Enum):
    NOT_READY = "NOT_READY"
    READY = "READY"
    TAKING_OFF = "TAKING_OFF"
    LANDING = "LANDING"
    HOVERING = "HOVERING"
    EXPLORING = "EXPLORING"
    RETURNING_BASE = "RETURNING_BASE"
    CRASHED = "CRASHED"


class DroneConnectionState(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class DroneType(str, Enum):
    ARGOS = "ARGOS"
    CRAZYFLIE = "CRAZYFLIE"


class DroneBattery(BaseModel):
    charge_percentage: int


class DroneVec3(BaseModel):
    x: float
    y: float
    z: float


class Orientation(BaseModel):
    yaw: float


class DroneRange(BaseModel):
    front: int
    back: int
    up: int
    left: int
    right: int
    bottom: int


class Drone(BaseModel):
    uuid: str
    state: DroneState
    type: DroneType
    battery: DroneBattery
    position: DroneVec3
    orientation: Orientation
    range: DroneRange
    connection_state: DroneConnectionState
