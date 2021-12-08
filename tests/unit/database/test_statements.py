import datetime
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.database.models import SavedMission
from backend.database.statements import (
    create_drone_metrics,
    create_drones_mission_association,
    create_new_mission,
    create_saved_map,
    get_all_missions,
    get_log_message,
    get_mission,
)
from backend.models.drone import DroneType
from backend.models.mission import Log, Mission, MissionState


# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


@pytest.fixture
def session_mock() -> Generator[MagicMock, None, None]:
    with patch("backend.database.statements.async_session") as mocked_session:
        yield mocked_session.return_value.__aenter__.return_value


@patch.object(SavedMission, "to_model")
async def test_create_mission(to_model_mock: MagicMock, session_mock: MagicMock) -> None:
    await create_new_mission(drone_type=DroneType.ARGOS)

    session_mock.add.assert_called()
    session_mock.commit.assert_awaited()
    session_mock.refresh.assert_awaited()
    to_model_mock.assert_called()


async def test_create_drone(session_mock: MagicMock) -> None:
    await create_drone_metrics(MagicMock(), 1)

    session_mock.add.assert_called()
    session_mock.commit.assert_awaited()


async def test_create_drone_mission_association(session_mock: MagicMock) -> None:
    await create_drones_mission_association(iter([MagicMock()]), 1)

    session_mock.add.assert_called()
    session_mock.commit.assert_awaited()


async def test_create_saved_map(session_mock: MagicMock) -> None:
    await create_saved_map(MagicMock())

    session_mock.add.assert_called()
    session_mock.commit.assert_awaited()


async def test_get_mission(session_mock: MagicMock) -> None:
    mission = Mission(
        id=1,
        drone_type=DroneType.CRAZYFLIE,
        state=MissionState.CREATED,
        total_distance=0,
        starting_time=datetime.datetime.utcnow(),
        ending_time=None,
    )

    response_mock = MagicMock()
    response_mock.scalars.return_value.first.return_value = mission
    session_mock.execute = AsyncMock(return_value=response_mock)
    result = await get_mission(1)

    assert result == mission
    session_mock.execute.assert_awaited()


async def test_get_all_missions(session_mock: MagicMock) -> None:
    mission = Mission(
        id=1,
        drone_type=DroneType.CRAZYFLIE,
        state=MissionState.CREATED,
        total_distance=0,
        starting_time=datetime.datetime.utcnow(),
        ending_time=None,
    )

    response_mock = MagicMock()
    response_mock.scalars.return_value.all.return_value = [mission]
    session_mock.execute = AsyncMock(return_value=response_mock)
    result = await get_all_missions()

    assert result == [mission]
    session_mock.execute.assert_awaited()


async def test_get_log_message(session_mock: MagicMock) -> None:
    log = Log(id=1, mission_id=1, timestamp=10, message="HELPMEPLZ")

    response_mock = MagicMock()
    response_mock.scalars.return_value = [log]
    session_mock.execute = AsyncMock(return_value=response_mock)
    result = await get_log_message(1, 0)

    assert result == [log]
    session_mock.execute.assert_awaited()
