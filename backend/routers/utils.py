from typing import Any, Type, Union

from backend.exceptions.response import ResponseException


def generate_responses_documentation(*args: Type[ResponseException]) -> dict[Union[int, str], dict[str, Any]]:
    return {exception.http_status_code(): {"description": exception.description()} for exception in args}
