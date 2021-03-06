from enum import IntEnum


class Command(IntEnum):
    TAKE_OFF = 0
    LAND = 1
    START_EXPLORATION = 2
    RETURN_TO_BASE = 3
    IDENTIFY = 4
    ACTIVATE_P2P = 5
    SET_POSITION = 6
