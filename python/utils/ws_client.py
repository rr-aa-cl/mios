import json
import websockets
import asyncio
import socket
from concurrent.futures import TimeoutError as ConnectionTimeoutError
import websockets.exceptions


async def send(hostname, port=8383, endpoint="mios/core", request=None, timeout=100, silent=False):
    uri = "ws://" + hostname + ":" + str(port) + "/" +endpoint
    try:
        async with websockets.connect(uri, close_timeout=1) as websocket:
            message = json.dumps(request)
            await websocket.send(message)
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            return json.loads(response)
    except ConnectionRefusedError as e:
        if silent is False:
            print("ConnectionRefusedError: ")
            print(e)
            print("Hostname: " + hostname + ", port: " + str(port) + ", endpoint: " + endpoint)
        return None
    except ConnectionResetError as e:
        if silent is False:
            print("ConnectionResetError: ")
            print(e)
            print("Hostname: " + hostname + ", port: " + str(port) + ", endpoint: " + endpoint)
        return None
    except ConnectionAbortedError as e:
        if silent is False:
            print("ConnectionAbortedError: ")
            print(e)
            print("Hostname: " + hostname + ", port: " + str(port) + ", endpoint: " + endpoint)
        return None
    except websockets.ConnectionClosedError as e:
        if silent is False:
            print("ConnectionClosedError: ")
            print(e)
            print("Hostname: " + hostname + ", port: " + str(port) + ", endpoint: " + endpoint)
        return None
    except ConnectionTimeoutError as e:
        if silent is False:
            print("ConnectionTimeoutError: ")
            print(e)
            print("Hostname: " + hostname + ", port: " + str(port) + ", endpoint: " + endpoint)
        return None
    except websockets.exceptions.InvalidMessage as e:
        if silent is False:
            print("InvalidMessage: ")
            print(e)
            print("Hostname: " + hostname + ", port: " + str(port) + ", endpoint: " + endpoint)
        return None


def call_server(hostname, port, endpoint, request, timeout):
    asyncio.set_event_loop(asyncio.new_event_loop())
    return asyncio.get_event_loop().run_until_complete(send(hostname, request=request, port=port,
                                                            endpoint=endpoint, timeout=timeout))


def call_method(hostname, method, payload=None, port=8383, endpoint="mios/core", timeout=100, silent=False):
    try:
        request = {
            "method": method,
            "request": payload
        }
        asyncio.set_event_loop(asyncio.new_event_loop())
        return asyncio.get_event_loop().run_until_complete(send(hostname, request=request, port=port,
                                                                endpoint=endpoint, timeout=timeout, silent=silent))
    except socket.gaierror as e:
        print(e)
        print("Hostname: " + hostname + ", port:" + str(port) + ", endpoint: " + endpoint)
        return None


def start_task(hostname, task, parameters={}, queue=False):
    payload = {
        "task": task,
        "parameters": parameters,
        "queue": queue
    }
    return call_method(hostname, "start_task", payload)


def stop_task(hostname, nominal=False, success=False, recover=False, empty_queue=False, cost_suc=0.0, cost_err=0.0):
    payload = {
        "nominal": nominal,
        "success": success,
        "recover": recover,
        "empty_queue": empty_queue,
        "cost_suc": cost_suc,
        "cost_err": cost_err
    }
    return call_method(hostname, "stop_task", payload)


def wait_for_task(hostname, task_uuid):
    payload = {
        "task_uuid": task_uuid
    }
    return call_method(hostname, "wait_for_task", payload)


def start_task_and_wait(hostname, task, parameters, queue=False):
    response = start_task(hostname, task, parameters, queue)
    response = wait_for_task(hostname, response["result"]["task_uuid"])
    return response


def short_teach_insertion(hostname, object, hole):
    call_method(hostname, "grasp_object",
             {"object": "none", "width": 0., "speed": 0.05, "force": 60., "check_width": False})
    call_method(hostname, "teach_object", {"object": object, "teach_width": True,
                                                              "reference_frame": "none", "is_reference_frame": False})
    call_method(hostname, "release_object", {"width": 0.05, "speed": 0.2})
    call_method(hostname, "grasp_object", {"object": object,"width":0.,"speed":0.05,"force":60.,"check_width":False})
    call_method(hostname, "teach_object", {"object": hole, "teach_width": False,
                                                              "reference_frame": "none", "is_reference_frame": False})
    call_method(hostname, "release_object",{"width":0.05,"speed":0.2})