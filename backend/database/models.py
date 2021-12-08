import base64
from typing import Final

import sqlalchemy
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint

from backend.database.database import Base
from backend.models.drone import Drone, DroneType
from backend.models.mission import Map, Mission, MissionState


class SavedDroneMetrics(Base):
    __tablename__: Final = "metrics"
    __table_args__: Final = (
        ForeignKeyConstraint(
            ("drone_id", "mission_id"), ("drone_mission_association.drone_id", "drone_mission_association.mission_id")
        ),
    )

    id = Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    x = Column(sqlalchemy.Float)
    y = Column(sqlalchemy.Float)
    z = Column(sqlalchemy.Float)
    yaw = Column(sqlalchemy.Float)
    front = Column(sqlalchemy.Float)
    back = Column(sqlalchemy.Float)
    up = Column(sqlalchemy.Float)
    left = Column(sqlalchemy.Float)
    right = Column(sqlalchemy.Float)
    bottom = Column(sqlalchemy.Float)
    drone_id = Column(sqlalchemy.Integer)
    mission_id = Column(sqlalchemy.Integer)


class SavedDrone(Base):
    __tablename__: Final = "drone"

    id = Column(sqlalchemy.Integer, primary_key=True, index=True)
    drone_type = Column(sqlalchemy.Enum(DroneType))


class SavedMission(Base):
    __tablename__: Final = "mission"

    id = Column(sqlalchemy.Integer, autoincrement=True, primary_key=True, index=True)
    drone_type = Column(sqlalchemy.Enum(DroneType))
    state = Column(sqlalchemy.Enum(MissionState), default=MissionState.CREATED)
    starting_time = Column(sqlalchemy.DateTime)
    total_distance = Column(sqlalchemy.Float)
    ending_time = Column(sqlalchemy.DateTime, nullable=True)

    def to_model(self) -> Mission:
        return Mission(
            id=self.id,
            drone_type=self.drone_type,
            state=self.state,
            total_distance=self.total_distance,
            starting_time=self.starting_time,
            ending_time=self.ending_time,
        )


class SavedMap(Base):
    __tablename__: Final = "map"

    mission_id = Column(sqlalchemy.Integer, ForeignKey("mission.id"), primary_key=True, index=True)
    map = Column(sqlalchemy.LargeBinary)

    def to_model(self) -> Map:
        return Map(mission_id=self.mission_id, map=base64.decodebytes(self.map))


class DroneMissionAssociation(Base):
    __tablename__: Final = "drone_mission_association"

    drone_id = Column(sqlalchemy.Integer, ForeignKey("drone.id"), primary_key=True)
    mission_id = Column(sqlalchemy.Integer, ForeignKey("mission.id"), primary_key=True)


class SavedLog(Base):
    __tablename__: Final = "log"

    id = Column(sqlalchemy.Integer, autoincrement=True, primary_key=True, index=True)
    mission_id = Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("mission.id"))
    timestamp = Column(sqlalchemy.DateTime)
    message = Column(sqlalchemy.String)
