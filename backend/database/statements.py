from collections import defaultdict
from datetime import datetime
from typing import Iterable

from fastapi.logger import logger
from sqlalchemy import select, update

from backend.database.database import async_session
from backend.database.models import (
    DroneMissionAssociation,
    SavedDrone,
    SavedDroneMetrics,
    SavedLog,
    SavedMap,
    SavedMission,
)
from backend.models.drone import DroneOrientation, DronePositionOrientationRange, DroneRange, DroneType, DroneVec3
from backend.models.mission import Log, Map, Mission, MissionState
from backend.registered_drone import RegisteredDrone


async def create_new_mission(drone_type: DroneType) -> Mission:
    async with async_session() as session:
        mission = SavedMission(
            drone_type=drone_type,
            state=MissionState.CREATED,
            total_distance=0,
            starting_time=datetime.utcnow(),
            ending_time=None,
        )
        session.add(mission)
        await session.commit()
        await session.refresh(mission)

    return mission.to_model()


async def get_mission(mission_id: int) -> Mission:
    async with async_session() as session:
        result = await session.execute(select(SavedMission).where(SavedMission.id == mission_id))
        saved_mission = result.scalars().first()

    if saved_mission is None:
        raise RuntimeError("Mission doesn't exist")

    return Mission(
        id=saved_mission.id,
        drone_type=saved_mission.drone_type,
        state=saved_mission.state,
        total_distance=saved_mission.total_distance,
        starting_time=saved_mission.starting_time,
        ending_time=saved_mission.ending_time,
    )


async def get_all_missions() -> list[Mission]:
    async with async_session() as session:
        result = await session.execute(select(SavedMission))
        saved_missions = result.scalars().all()

    return [
        Mission(
            id=saved_mission.id,
            drone_type=saved_mission.drone_type,
            state=saved_mission.state,
            total_distance=saved_mission.total_distance,
            starting_time=saved_mission.starting_time,
            ending_time=saved_mission.ending_time,
        )
        for saved_mission in saved_missions
    ]


async def update_mission_state(mission_id: int, mission_state: MissionState) -> Mission:
    async with async_session() as session:
        statement = update(SavedMission).where(SavedMission.id == mission_id).values(state=mission_state)
        await session.execute(statement)
        await session.commit()

    return await get_mission(mission_id)


async def end_mission(mission_id: int, total_distance: float) -> Mission:
    async with async_session() as session:
        statement = (
            update(SavedMission)
            .where(SavedMission.id == mission_id)
            .values(state=MissionState.ENDED, total_distance=total_distance, ending_time=datetime.utcnow())
        )
        await session.execute(statement)
        await session.commit()

    return await get_mission(mission_id)


async def insert_log_in_database(log_message: SavedLog) -> None:
    async with async_session() as session:
        try:
            session.add(log_message)
            await session.commit()
        except Exception as e:
            logger.error(e)


async def get_log_message(mission_id: int, starting_id: int) -> list[Log]:
    async with async_session() as session:
        statement = select(SavedLog).filter(SavedLog.mission_id == mission_id, SavedLog.id >= starting_id)
        rows = await session.execute(statement)

        return [
            Log(id=row.id, mission_id=row.mission_id, timestamp=row.timestamp, message=row.message)
            for row in rows.scalars()
        ]


async def create_drone(drone: RegisteredDrone) -> None:
    async with async_session() as session:
        drone = SavedDrone(id=drone.id, drone_type=drone.drone_type)
        session.add(drone)
        await session.commit()


async def create_drone_metrics(drone: RegisteredDrone, mission_id: int) -> None:
    async with async_session() as session:
        metric = SavedDroneMetrics(
            x=drone.position.x,
            y=drone.position.y,
            z=drone.position.z,
            yaw=drone.orientation.yaw,
            front=drone.range.front,
            back=drone.range.back,
            up=drone.range.up,
            left=drone.range.left,
            right=drone.range.right,
            bottom=drone.range.bottom,
            drone_id=drone.id,
            mission_id=mission_id,
        )
        session.add(metric)
        await session.commit()


async def create_drones_mission_association(drones: Iterable[RegisteredDrone], mission_id: int) -> None:
    async with async_session() as session:
        for drone in drones:
            association = DroneMissionAssociation(drone_id=drone.id, mission_id=mission_id)
            session.add(association)
        await session.commit()


async def get_drones_metadata(mission_id: int) -> dict[int, list[DronePositionOrientationRange]]:
    async with async_session() as session:
        statement = select(SavedDroneMetrics).filter(SavedDroneMetrics.mission_id == mission_id)
        rows = await session.execute(statement)

    metrics = defaultdict(list)
    for row in rows.scalars():
        metrics[row.drone_id].append(
            DronePositionOrientationRange(
                position=DroneVec3(x=row.x, y=row.y, z=row.z),
                orientation=DroneOrientation(yaw=row.yaw),
                range=DroneRange(
                    front=row.front, back=row.back, up=row.up, left=row.left, right=row.right, bottom=row.bottom
                ),
            )
        )

    return metrics


async def create_saved_map(map_to_save: Map) -> None:
    async with async_session() as session:
        saved_map = SavedMap(mission_id=map_to_save.mission_id, map=map_to_save.map.encode("ascii"))
        session.add(saved_map)
        await session.commit()


async def get_saved_map(mission_id: int) -> Map:
    async with async_session() as session:
        statement = select(SavedMap).filter(SavedMap.id == mission_id)
        results = await session.execute(statement)
        saved_map = results.scalars().first()

    return Map(id=saved_map.mission_id, map=saved_map.map.decode("ascii"))
