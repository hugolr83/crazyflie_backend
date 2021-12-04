from enum import Enum

from pydantic import BaseModel


class DroneState(str, Enum):
    NOT_READY = "NOT READY"
    READY = "READY"
    TAKING_OFF = "TAKING OFF"
    LANDING = "LANDING"
    HOVERING = "HOVERING"
    EXPLORING = "EXPLORING"
    RETURNING_BASE = "RETURNING BASE"
    CRASHED = "CRASHED"


class DroneType(str, Enum):
    ARGOS = "ARGOS"
    CRAZYFLIE = "CRAZYFLIE"


class DroneBattery(BaseModel):
    charge_percentage: int


class DroneVec3(BaseModel):
    x: float
    y: float
    z: float


class DroneOrientation(BaseModel):
    yaw: float


class DroneRange(BaseModel):
    front: int
    back: int
    up: int
    left: int
    right: int
    bottom: int


class Drone(BaseModel):
    id: int
    state: DroneState
    type: DroneType
    battery: DroneBattery
    position: DroneVec3
    orientation: DroneOrientation
    range: DroneRange
    total_distance: float


class DronePositionOrientation(BaseModel):
    position: DroneVec3
    orientation: DroneOrientation


class DronePositionOrientationRange(BaseModel):
    position: DroneVec3
    orientation: DroneOrientation
    range: DroneRange
