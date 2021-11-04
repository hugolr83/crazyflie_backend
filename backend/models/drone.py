from enum import Enum, IntEnum

from pydantic import BaseModel


class DroneState(IntEnum):
    NOT_READY = 0
    READY = 1
    TAKING_OFF = 2
    LANDING = 3
    HOVERING = 4
    EXPLORING = 5
    RETURNING_BASE = 6
    CRASHED = 7


class DroneType(str, Enum):
    ARGOS = "ARGOS"
    CRAZYFLIE = "CRAZYFLIE"


class DroneBattery(BaseModel):
    charge_percentage: int


class DroneVec3(BaseModel):
    x: float
    y: float
    z: float


class DroneRange(BaseModel):
    front: int
    back: int
    up: int
    left: int
    right: int
    bottom: int


class Drone(BaseModel):
    uuid: str
    state: str
    type: DroneType
    battery: DroneBattery
    position: DroneVec3
    range: DroneRange
