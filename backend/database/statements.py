from datetime import datetime

from fastapi.logger import logger
from sqlalchemy import select, update

from backend.database.database import async_session
from backend.database.models import SavedLog, SavedMission
from backend.models.drone import DroneType
from backend.models.mission import Log, Mission, MissionState


async def create_new_mission(drone_type: DroneType) -> Mission:
    async with async_session() as session:
        mission = SavedMission(
            drone_type=drone_type, state=MissionState.CREATED, starting_time=datetime.now(), ending_time=None
        )
        session.add(mission)
        await session.commit()
        await session.refresh(mission)

    return mission.to_model()


async def get_mission(mission_id: int) -> Mission:
    async with async_session() as session:
        result = await session.execute(select(SavedMission).where(SavedMission.id == mission_id))
        saved_mission = result.scalars().first()

    return Mission(
        id=saved_mission.id,
        drone_type=saved_mission.drone_type,
        state=saved_mission.state,
        starting_time=saved_mission.starting_time,
        ending_time=saved_mission.ending_time,
    )


async def get_and_update_mission_state(mission_id: int, mission_state: MissionState) -> Mission:
    async with async_session() as session:
        statement = update(SavedMission).where(SavedMission.id == mission_id).values(state=mission_state)
        await session.execute(statement)
        await session.commit()
        result = await session.execute(select(SavedMission).where(SavedMission.id == mission_id))
        saved_mission = result.scalars().first()

    return Mission(
        id=saved_mission.id,
        drone_type=saved_mission.drone_type,
        state=saved_mission.state,
        starting_time=saved_mission.starting_time,
        ending_time=saved_mission.ending_time,
    )


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
