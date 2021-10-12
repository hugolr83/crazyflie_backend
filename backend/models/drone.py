from enum import Enum

from pydantic import BaseModel


class DroneState(str, Enum):
    WAITING = "WAITING"
    STARTING = "STARTING"
    NAVIGATING = "NAVIGATING"
    CRASHED = "CRASHED"
    LANDING = "LANDING"


class DroneType(str, Enum):
    ARGOS = "ARGOS"
    CRAZYFLIE = "CRAZYFLIE"


class DroneBattery(BaseModel):
    charge_percentage: int
    voltage: float


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
    state: DroneState
    type: DroneType
    battery: DroneBattery
    position: DroneVec3
    range: DroneRange
