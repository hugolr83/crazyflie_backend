from typing import Final

import sqlalchemy
from sqlalchemy import Column

from backend.database.database import Base
from backend.models.drone import DroneType
from backend.models.mission import Mission, MissionState


class SavedMission(Base):  # type: ignore[misc]
    __tablename__: Final = "mission"

    id = Column(sqlalchemy.Integer, autoincrement=True, primary_key=True, index=True)
    drone_type = Column(sqlalchemy.Enum(DroneType))
    state = Column(sqlalchemy.Enum(MissionState), default=MissionState.CREATED)
    starting_time = Column(sqlalchemy.DateTime)
    ending_time = Column(sqlalchemy.DateTime, nullable=True)

    def to_model(self) -> Mission:
        return Mission(
            id=self.id,
            drone_type=self.drone_type,
            state=self.state,
            starting_time=self.starting_time,
            ending_time=self.ending_time,
        )


class SavedLog(Base):  # type: ignore[misc]
    __tablename__: Final = "log"

    id = Column(sqlalchemy.Integer, autoincrement=True, primary_key=True, index=True)
    mission_id = Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("mission.id"))
    timestamp = Column(sqlalchemy.DateTime)
    message = Column(sqlalchemy.String)
