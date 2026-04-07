"""
test_ws_client.py – Phase 0 baseline + Phase 2 modernisation tests.

Uses pytest-asyncio and a mock websocket server to avoid real network calls.
All tests run without a live mios agent.
"""
import asyncio
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_response(success=True, task_uuid="uuid-1"):
    return json.dumps({
        "result": {
            "result": success,
            "task_uuid": task_uuid,
            "task_result": {
                "success": success,
                "time": 1.0,
                "contact_forces": 5.0,
                "heuristic": 0.0,
                "error_codes": [],
            },
            "error": ""
        }
    })


# ---------------------------------------------------------------------------
# call_method signature smoke test
# ---------------------------------------------------------------------------
class TestCallMethodSignature:
    def test_call_method_is_callable(self):
        from utils.ws_client import call_method
        assert callable(call_method)

    def test_call_method_returns_none_on_connection_refused(self):
        """When no server is listening, call_method must return None (not raise)."""
        from utils.ws_client import call_method
        result = call_method(
            hostname="127.0.0.1",
            port=19999,   # nothing listening here
            method="ping",
            payload=None,
            silent=True,
            timeout=1,
        )
        assert result is None


# ---------------------------------------------------------------------------
# send() async function with mocked websocket
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_send_returns_parsed_json():
    """send() must parse the JSON response and return a dict."""
    from utils import ws_client

    canned = make_response(success=True)

    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock(return_value=canned)
    mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
    mock_ws.__aexit__ = AsyncMock(return_value=False)

    with patch("utils.ws_client.websockets.connect", return_value=mock_ws):
        result = await ws_client.send(
            hostname="localhost",
            port=12000,
            endpoint="mios/core",
            request={"method": "ping", "request": None},
            timeout=5,
        )

    assert result is not None
    assert "result" in result


@pytest.mark.asyncio
async def test_send_returns_none_on_connection_refused():
    """send() must return None when the connection is refused."""
    from utils import ws_client

    with patch("utils.ws_client.websockets.connect", side_effect=ConnectionRefusedError("refused")):
        result = await ws_client.send(
            hostname="localhost",
            port=12000,
            endpoint="mios/core",
            request={"method": "ping", "request": None},
            timeout=5,
            silent=True,
        )

    assert result is None


# ---------------------------------------------------------------------------
# start_task / wait_for_task helpers
# ---------------------------------------------------------------------------
class TestHelperFunctions:
    def test_start_task_builds_correct_payload(self):
        from utils.ws_client import start_task
        with patch("utils.ws_client.call_method") as mock_call:
            mock_call.return_value = {"result": {"task_uuid": "u1", "result": True}}
            response = start_task("robot01", "TaxInsertion", {"key": "val"}, queue=False)
            called_payload = mock_call.call_args[0][3]
            assert called_payload["task"] == "TaxInsertion"
            assert called_payload["parameters"] == {"key": "val"}
            assert called_payload["queue"] is False

    def test_wait_for_task_builds_correct_payload(self):
        from utils.ws_client import wait_for_task
        with patch("utils.ws_client.call_method") as mock_call:
            mock_call.return_value = {"result": {"result": True}}
            wait_for_task("robot01", "task-uuid-123")
            called_payload = mock_call.call_args[0][3]
            assert called_payload["task_uuid"] == "task-uuid-123"
