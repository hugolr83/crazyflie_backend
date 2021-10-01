import os
from typing import Any, Type, Union

from backend.exceptions.response import ResponseException


def get_environment_variable_or_raise(environment_variable: str) -> str:
    if not (value := os.getenv(environment_variable)):
        raise EnvironmentError(f"{environment_variable} must be defined")
    return value


def generate_responses_documentation(*args: Type[ResponseException]) -> dict[Union[int, str], dict[str, Any]]:
    return {exception.http_status_code(): {"description": exception.description()} for exception in args}
