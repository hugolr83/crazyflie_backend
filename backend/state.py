from enum import Enum


class DroneState(str, Enum):
    WAITING = "WAITING"
    STARTING = "STARTING"
    NAVIGATING = "NAVIGATING"
    CRASHED = "CRASHED"
    LANDING = "LANDING"
