import base64
import datetime

from backend.database.models import SavedDrone, SavedMap, SavedMission
from backend.models.drone import DroneType
from backend.models.mission import Map, Mission, MissionState


def test_saved_mission_to_model() -> None:
    saved_mission = SavedMission(
        id=1,
        drone_type=DroneType.ARGOS,
        state=MissionState.CREATED,
        starting_time=datetime.datetime.utcnow(),
        total_distance=2.2,
        ending_time=None,
    )

    assert saved_mission.to_model() == Mission(
        id=saved_mission.id,
        drone_type=saved_mission.drone_type,
        state=saved_mission.state,
        total_distance=saved_mission.total_distance,
        starting_time=saved_mission.starting_time,
        ending_time=saved_mission.ending_time,
    )


def test_saved_map_to_model() -> None:
    saved_map = SavedMap(mission_id=1, map="YWJj".encode("utf8"))

    assert saved_map.to_model() == Map(mission_id=saved_map.mission_id, map=base64.decodebytes("YWJj".encode("utf8")))
