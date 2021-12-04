from http import HTTPStatus
from typing import Sequence

from fastapi import HTTPException

from backend.models.drone import DroneType
from backend.models.mission import MissionState


class ResponseException(HTTPException):
    @classmethod
    def http_status_code(cls) -> int:
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def description(cls) -> str:
        raise NotImplementedError  # pragma: no cover


class DroneNotFoundException(ResponseException):
    def __init__(self, drone_id: int) -> None:
        super().__init__(
            status_code=self.http_status_code(),
            detail=f"Drone with id {drone_id} doesn't exist or isn't registered anymore",
        )

    @classmethod
    def http_status_code(cls) -> int:
        return int(HTTPStatus.NOT_FOUND)

    @classmethod
    def description(cls) -> str:
        return "Drone doesn't exist or isn't registered anymore"


class WrongDroneTypeException(ResponseException):
    def __init__(self, drone_type: DroneType) -> None:
        super().__init__(
            status_code=self.http_status_code(),
            detail=f"API call is not supported on {drone_type.value} drones",
        )

    @classmethod
    def http_status_code(cls) -> int:
        return int(HTTPStatus.BAD_REQUEST)

    @classmethod
    def description(cls) -> str:
        return "API call is not supported on the provided drone type"


class InvalidMissionStateException(ResponseException):
    def __init__(
        self,
        current_state: MissionState,
        desired_state: MissionState,
        allowed_states: Sequence[MissionState],
    ) -> None:
        super().__init__(
            status_code=self.http_status_code(),
            detail=(
                f"Impossible to set state {desired_state.name} since current mission state is "
                f"{current_state}. Current state must be "
                f"{', '.join((allowed_mission_state.name for allowed_mission_state in allowed_states))}"
            ),
        )

    @classmethod
    def http_status_code(cls) -> int:
        return int(HTTPStatus.BAD_REQUEST)

    @classmethod
    def description(cls) -> str:
        return "Mission state transition isn't possible"


class MissionIsAlreadyActiveException(ResponseException):
    def __init__(self, existing_mission_id: int, drone_type: DroneType) -> None:
        super().__init__(
            status_code=self.http_status_code(),
            detail=f"Active mission for drone type {drone_type.name} already exists (id: {existing_mission_id})",
        )

    @classmethod
    def http_status_code(cls) -> int:
        return int(HTTPStatus.BAD_REQUEST)

    @classmethod
    def description(cls) -> str:
        return "A mission for that drone type is already existing"
