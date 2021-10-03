from enum import Enum

from pydantic import BaseModel

from backend.state import DroneState


class DroneType(str, Enum):
    ARGOS = "ARGOS"
    CRAZYFLIE = "CRAZYFLIE"


class Drone(BaseModel):
    uuid: str
    state: DroneState
    type: DroneType
