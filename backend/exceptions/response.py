from http import HTTPStatus

from fastapi import HTTPException

from backend.models.drone import DroneType


class ResponseException(HTTPException):
    @classmethod
    def http_status_code(cls) -> int:
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def description(cls) -> str:
        raise NotImplementedError  # pragma: no cover


class DroneNotFoundException(ResponseException):
    def __init__(self, uuid: str) -> None:
        super().__init__(
            status_code=self.http_status_code(),
            detail=f"Drone with uuid {uuid} doesn't exist or isn't registered anymore",
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
