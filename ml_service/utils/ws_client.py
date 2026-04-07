import json
import websockets
import asyncio
import socket
import logging
import time
from typing import Optional, Any
import websockets.exceptions
from utils.mios_errors import MiosConnectionError, MiosProtocolError, MiosTimeoutError

logger = logging.getLogger("ml_service")


async def _async_send(hostname: str, port: int, endpoint: str, request: dict, timeout: float) -> dict:
    """Internal async function to handle the websocket communication."""
    uri = f"ws://{hostname}:{port}/{endpoint}"
    async with websockets.connect(uri, close_timeout=timeout) as websocket:
        message = json.dumps(request)
        await websocket.send(message)
        response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise MiosProtocolError(f"Malformed JSON response from {hostname}: {e}")


async def send(hostname: str, port: int = 12000, endpoint: str = "mios/core", 
               request: Optional[dict] = None, timeout: float = 100, silent: bool = False,
               max_retries: int = 3) -> Optional[dict]:
    """
    Sends a request via WebSocket with exponential backoff retry logic.
    Returns the parsed JSON response or None if all retries failed.
    """
    if request is None:
        request = {}

    attempt = 0
    while attempt < max_retries:
        try:
            return await _async_send(hostname, port, endpoint, request, timeout)
        except (ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError, 
                websockets.exceptions.ConnectionClosedError, socket.gaierror) as e:
            if not silent:
                logger.warning("Agent %s:%s connection failed (attempt %d/%d): %s", 
                               hostname, port, attempt + 1, max_retries, e)
        except (asyncio.TimeoutError, websockets.exceptions.InvalidMessage) as e:
             if not silent:
                logger.warning("Agent %s:%s timeout or invalid message (attempt %d/%d): %s", 
                               hostname, port, attempt + 1, max_retries, e)
        except Exception as e:
            if not silent:
                logger.error("Unexpected error communicating with Agent %s:%s: %s", 
                             hostname, port, e)
            return None

        attempt += 1
        if attempt < max_retries:
            await asyncio.sleep(2 ** attempt * 0.1)  # Exponential backoff: 0.2s, 0.4s...

    return None


def call_method(hostname: str, port: int, method: str, payload: Any = None, 
                endpoint: str = "mios/core", timeout: float = 100, silent: bool = False) -> Optional[dict]:
    """Synchronous wrapper for sending a method call to a mios agent."""
    request = {
        "method": method,
        "request": payload
    }
    try:
        return asyncio.run(send(hostname, port, endpoint, request, timeout, silent))
    except Exception as e:
        if not silent:
            logger.error("Failed to call method %s on %s:%s: %s", method, hostname, port, e)
        return None


def call_server(hostname: str, port: int, endpoint: str, request: dict, timeout: float) -> Optional[dict]:
    """Synchronous wrapper for sending a raw request to a mios server."""
    return asyncio.run(send(hostname, port, endpoint, request, timeout))


def start_task(hostname: str, task: str, parameters: dict = {}, queue: bool = False, port: int = 12000) -> Optional[dict]:
    payload = {
        "task": task,
        "parameters": parameters,
        "queue": queue
    }
    return call_method(hostname, port, "start_task", payload)


def stop_task(hostname: str, raise_exception: bool = False, recover: bool = False, 
              empty_queue: bool = False, port: int = 12000) -> Optional[dict]:
    payload = {
        "raise_exception": raise_exception,
        "recover": recover,
        "empty_queue": empty_queue
    }
    return call_method(hostname, port, "stop_task", payload)


def wait_for_task(hostname: str, task_uuid: str, port: int = 12000, timeout: float = 100) -> Optional[dict]:
    payload = {
        "task_uuid": task_uuid
    }
    return call_method(hostname, port, "wait_for_task", payload, timeout=timeout)


def start_task_and_wait(hostname: str, task: str, parameters: dict, queue: bool = False) -> Optional[dict]:
    response = start_task(hostname, task, parameters, queue)
    if response and "result" in response and "task_uuid" in response["result"]:
        return wait_for_task(hostname, response["result"]["task_uuid"])
    return response


def short_teach_insertion(hostname: str, object_name: str, hole_name: str):
    """Note: Original had redundant/untyped args; preserved logic."""
    call_method(hostname, 12000, "grasp_object",
                {"object": "none", "width": 0., "speed": 0.05, "force": 60., "check_width": False})
    call_method(hostname, 12000, "teach_object", 
                {"object": object_name, "teach_width": True, "reference_frame": "none", "is_reference_frame": False})
    call_method(hostname, 12000, "release_object", {"width": 0.05, "speed": 0.2})
    call_method(hostname, 12000, "grasp_object", 
                {"object": object_name, "width": 0., "speed": 0.05, "force": 60., "check_width": False})
    call_method(hostname, 12000, "teach_object", 
                {"object": hole_name, "teach_width": False, "reference_frame": "none", "is_reference_frame": False})
    call_method(hostname, 12000, "release_object", {"width": 0.05, "speed": 0.2})
