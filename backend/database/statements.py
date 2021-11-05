from datetime import datetime

from sqlalchemy import select, update

from backend.database.database import async_session
from backend.database.models import SavedLog, SavedMission
from backend.models.drone import DroneType
from backend.models.mission import Log, Mission, MissionState


async def create_new_mission(drone_type: DroneType) -> Mission:
    async with async_session() as session:
        mission = SavedMission(
            drone_type=drone_type, status=MissionState.CREATED, starting_time=datetime.now(), ending_time=None
        )
        session.add(mission)
        await session.commit()
        await session.refresh(mission)

    return mission.to_model()


async def start_existing_mission(mission_id: int) -> None:
    async with async_session() as session:
        statement = update(SavedMission).where(SavedMission.id == mission_id).values(status=MissionState.STARTED)
        await session.execute(statement)
        await session.commit()


async def insert_log_in_database(log_message: SavedLog) -> None:
    async with async_session() as session:
        try:
            session.add(log_message)
            await session.commit()
        except Exception as e:
            print(e)


async def get_log_message(starting_id: int) -> list[Log]:
    async with async_session() as session:
        statement = select(SavedMission).filter(SavedMission.id >= starting_id)
        rows = await session.execute(statement)

    return [Log(id=row.id, mission_id=row.mission_id, timestamp=row.timestamp, message=row.text) for row in rows]
