import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from backend.models.drone import DroneType


class MissionState(str, Enum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    ENDED = "ENDED"


class Mission(BaseModel):
    id: int
    drone_type: DroneType
    state: MissionState = MissionState.CREATED
    starting_time: datetime.datetime
    ending_time: Optional[datetime.datetime] = None


class Log(BaseModel):
    id: int
    mission_id: int
    timestamp: datetime.datetime
    text: str
