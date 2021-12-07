from typing import Optional

from fastapi import APIRouter

from backend.communication.command import Command
from backend.communication.communication import send_command_to_all_drones
from backend.database.statements import (
    create_drones_mission_association,
    create_new_mission,
    create_saved_map,
    get_all_missions,
    get_drones_metadata,
    get_log_message,
    get_mission,
    get_saved_map,
    update_mission_state,
)
from backend.exceptions.response import (
    DroneNotFoundException,
    InvalidMissionStateException,
    MissionIsAlreadyActiveException,
)
from backend.models.drone import Drone, DronePositionOrientation, DronePositionOrientationRange, DroneType
from backend.models.mission import Log, Map, Mission, MissionState
from backend.registry import get_registry
from backend.routers.utils import generate_responses_documentation

router = APIRouter(tags=["common"])


@router.get("/drones", operation_id="get_drones", response_model=list[Drone])
async def drones(drone_type: Optional[DroneType] = None) -> list[Drone]:
    """Retrieve all the currently registered drones. You can also filter which type of drone you want."""
    return list(map(lambda drone: drone.to_model(), get_registry().get_drones(drone_type)))


@router.get(
    "/drones/metadata",
    operation_id="get_drones_metadata",
    response_model=dict[int, list[DronePositionOrientationRange]],
)
async def drones_metadata(mission_id: int) -> dict[int, list[DronePositionOrientationRange]]:
    """Retrieve all the currently registered drones. You can also filter which type of drone you want."""
    return await get_drones_metadata(mission_id)


@router.post(
    "/drone/position",
    operation_id="set_drone_position",
    response_model=Drone,
    responses=generate_responses_documentation(DroneNotFoundException),
)
async def set_drone_position(drone_id: int, new_position: DronePositionOrientation) -> Drone:
    drone = get_registry().get_drone(drone_id)
    if not drone:
        raise DroneNotFoundException(drone_id)

    await drone.set_position(new_position)
    return drone.to_model()


@router.get("/logs", operation_id="get_logs", response_model=list[Log])
async def get_logs(mission_id: int, starting_id: int = 0) -> list[Log]:
    return await get_log_message(mission_id, starting_id)


@router.get("/map", operation_id="get_map", response_model=Map)
async def get_map(mission_id: int) -> Map:
    return await get_saved_map(mission_id)


@router.post("/map", operation_id="create_map", response_model=int)
async def create_map(map_to_save: Map) -> int:
    await create_saved_map(map_to_save)
    return map_to_save.mission_id


@router.get("/mission", operation_id="get_active_mission", response_model=Mission)
async def get_active_mission(drone_type: DroneType) -> Optional[Mission]:
    """Return the current active mission for a drone type, if it exists"""
    if mission_id := get_registry().get_active_mission_id(drone_type):
        return await get_mission(mission_id)
    else:
        return None


@router.get("/missions", operation_id="get_missions", response_model=list[Mission])
async def get_missions() -> list[Mission]:
    """Return the previously created missions"""
    return await get_all_missions()


@router.post("/mission", operation_id="create_mission", response_model=Mission)
async def create_mission(drone_type: DroneType) -> Mission:
    """Create a new mission"""
    mission = await create_new_mission(drone_type)
    return mission


async def ensure_valid_state(
    mission: Mission, desired_state: MissionState, allowed_states: list[MissionState]
) -> Mission:
    if mission.state not in allowed_states:
        raise InvalidMissionStateException(mission.state, desired_state, allowed_states)

    return mission


@router.post(
    "/start_mission",
    operation_id="start_mission",
    response_model=list[Drone],
    responses=generate_responses_documentation(MissionIsAlreadyActiveException, InvalidMissionStateException),
)
async def start_mission(mission_id: int) -> list[Drone]:
    """Start the mission for a specific drone type. Will communicate with all registered drones of that type."""
    mission = await get_mission(mission_id)
    await ensure_valid_state(mission, desired_state=MissionState.STARTED, allowed_states=[MissionState.CREATED])

    registry = get_registry()
    if current_mission_id := registry.get_active_mission_id(mission.drone_type):
        raise MissionIsAlreadyActiveException(current_mission_id, mission.drone_type)
    registry.set_active_mission_id(mission_id, mission.drone_type)

    mission = await update_mission_state(mission_id, MissionState.STARTED)
    selected_drones = list(get_registry().get_drones(mission.drone_type))
    await create_drones_mission_association(selected_drones, mission_id)
    for drone in selected_drones:
        drone.active_mission_id = mission_id
        drone.total_distance = 0.0

    return await send_command_to_all_drones(Command.START_EXPLORATION, selected_drones, mission_id)


async def process_mission_termination(mission_id: int, desired_state: MissionState, command: Command) -> list[Drone]:
    mission = await get_mission(mission_id)
    await ensure_valid_state(mission, desired_state, allowed_states=[MissionState.STARTED])

    mission = await update_mission_state(mission_id, desired_state)
    selected_drones = list(get_registry().get_drones(mission.drone_type))
    for drone in selected_drones:
        drone.active_mission_id = None

    return await send_command_to_all_drones(command, selected_drones, mission_id)


@router.post(
    "/end_mission",
    operation_id="end_mission",
    response_model=list[Drone],
    responses=generate_responses_documentation(InvalidMissionStateException),
)
async def end_mission(mission_id: int) -> list[Drone]:
    """End the mission (immediate landing) for a specific drone type. Will communicate with all registered drones of
    that type.
    """
    return await process_mission_termination(mission_id, MissionState.PENDING_ENDED, Command.LAND)


@router.post(
    "/return_to_base",
    operation_id="return_to_base",
    response_model=list[Drone],
    responses=generate_responses_documentation(InvalidMissionStateException),
)
async def return_to_base(mission_id: int) -> list[Drone]:
    """Return to base for a specific drone type. Will communicate with all registered drones of that type."""
    return await process_mission_termination(mission_id, MissionState.RETURNED_TO_BASE, Command.RETURN_TO_BASE)


# Related to https://github.com/OpenAPITools/openapi-generator/issues/6804
@router.get("/openapi-generator-workaround", response_model=DronePositionOrientationRange, deprecated=True)
async def openapi_generator_workaround() -> DronePositionOrientationRange:
    """Workaround for the issue where DronePositionOrientationRange wouldn't be imported within the generated
    API client."""
    raise NotImplementedError("This is not a real endpoint, only a workaround for fixing our OpenAPI schema")
