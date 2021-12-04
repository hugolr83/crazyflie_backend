from dataclasses import dataclass
from http import HTTPStatus
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from backend.communication.command import Command
from backend.registry import Registry
from tests.functional.conftest import ARGOS_ID, CRAZYFLIE_ID


@dataclass()
class IdentifyErrorHandlingTestCase:
    id: int
    status_code: int


@pytest.fixture()
def get_registry_mock(registry_mock: Registry) -> Generator[Registry, None, None]:
    with patch("backend.routers.crazyflie.get_registry") as patched_get_registry:
        patched_get_registry.return_value = registry_mock
        yield registry_mock


@pytest.mark.parametrize(
    "test_case",
    [
        IdentifyErrorHandlingTestCase(ARGOS_ID, HTTPStatus.BAD_REQUEST),
        IdentifyErrorHandlingTestCase(100, HTTPStatus.NOT_FOUND),
    ],
)
def test_error_handling_on_identify(
    get_registry_mock: Registry,
    test_case: IdentifyErrorHandlingTestCase,
    mocked_crazyflie_link: MagicMock,
    test_client: TestClient,
) -> None:
    response = test_client.post(f"/crazyflie/identify?drone_id={test_case.id}")
    assert response.status_code == test_case.status_code
    mocked_crazyflie_link.send_command.assert_not_called()


def test_identify_crazyflie(
    get_registry_mock: MagicMock, mocked_crazyflie_link: MagicMock, test_client: TestClient
) -> None:
    response = test_client.post(f"/crazyflie/identify?drone_id={CRAZYFLIE_ID}")
    assert response.status_code == HTTPStatus.OK
    mocked_crazyflie_link.send_command.assert_called_with(Command.IDENTIFY)
