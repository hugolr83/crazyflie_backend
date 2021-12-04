import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from backend.models.drone import DroneType


class MissionState(str, Enum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    PENDING_ENDED = "PENDING_ENDED"
    ENDED = "ENDED"
    RETURNED_TO_BASE = "RETURNED_TO_BASE"


class Mission(BaseModel):
    id: int
    drone_type: DroneType
    state: MissionState = MissionState.CREATED
    total_distance: float
    starting_time: datetime.datetime
    ending_time: Optional[datetime.datetime] = None


class Log(BaseModel):
    id: int
    mission_id: int
    timestamp: datetime.datetime
    message: str
