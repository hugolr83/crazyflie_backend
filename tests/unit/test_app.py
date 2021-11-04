from unittest.mock import MagicMock, patch

import pytest
from coveo_settings.mock import mock_config_value

from backend.app import ONLY_SERVE_OPENAPI_SCHEMA, shutdown_event, startup_event

# All test coroutines will be treated as marked
pytestmark = pytest.mark.asyncio


@patch("backend.app.initiate_links")
@patch("backend.app.initiate_tasks")
@pytest.mark.parametrize("only_serve_schema", [True, False])
async def test_resources_are_initiated_on_startup(
    initiate_links_mock: MagicMock, initiate_tasks_mock: MagicMock, only_serve_schema: bool
) -> None:
    with mock_config_value(ONLY_SERVE_OPENAPI_SCHEMA, only_serve_schema):
        await startup_event()

    if only_serve_schema:
        initiate_links_mock.assert_not_called()
        initiate_tasks_mock.assert_not_called()
    else:
        initiate_links_mock.assert_called()
        initiate_tasks_mock.assert_called()


@patch("backend.app.terminate_links")
@patch("backend.app.terminate_tasks")
@pytest.mark.parametrize("only_serve_schema", [True, False])
async def test_resources_are_terminated_on_shutdown(
    terminate_links_mock: MagicMock, terminate_tasks_mock: MagicMock, only_serve_schema: bool
) -> None:
    with mock_config_value(ONLY_SERVE_OPENAPI_SCHEMA, only_serve_schema):
        await shutdown_event()

    if only_serve_schema:
        terminate_links_mock.assert_not_called()
        terminate_tasks_mock.assert_not_called()
    else:
        terminate_links_mock.assert_called()
        terminate_tasks_mock.assert_called()
