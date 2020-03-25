import requests
import json
import websockets
import asyncio

def rpc_call(url, method, params=None, timeout=100):
    headers = {'content-type': 'application/json'}

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
    }
    print(payload)
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=timeout).json()
    except requests.Timeout:
        print('Timeout, server has terminated or does not exist.')
        response = None
    except requests.ConnectionError:
        print('Connection error, target url not reachable.')
        response = None

    return response


def start_task(url, task, params=None, queue=False):
    params = {
        'task': task,
        'queue': queue,
        'parameters': params if params else {}
    }
    r = rpc_call('http://' + url + ':8383', 'start_task', params)
    print(r)


def start_task_and_wait(url, task, params=None, queue=False):
    params = {
        'task': task,
        'queue': queue,
        'parameters': params if params else {}
    }
    r=rpc_call('http://' + url + ':8383', 'start_task', params)
    print(r)
    params = {
        'task_uuid': r["result"]["task_uuid"]
    }
    input('Press')
    r = rpc_call('http://' + url + ':8383', 'wait_for_task', params)
    print(r)


def stop_task(url, nominal=False, success=False, recover=True, empty_queue=False, cost_suc=0.0, cost_err=0.0):
    params={
        'nominal': nominal,
        'success': success,
        'recover': recover,
        "empty_queue": empty_queue,
        'cost_suc': cost_suc,
        'cost_err': cost_err
    }
    r = rpc_call('http://' + url + ':8383', 'stop_task', params)
    print(r)


def learn_task(url_service, problem_class, identity_instance, method_id, url_agents,
               preknowledge=None, mode=0, tags=[], setup=True, terminate=True, hosts=None):
    params = {
        'urls': url_agents,
        'problem_class': problem_class,
        "identity_instance": identity_instance,
        'method_id': method_id,
        "preknowledge": preknowledge,
        "setup": setup,
        "terminate": terminate,
        "mode": mode,
        "hosts": hosts,
        "tags": tags
    }

    response = rpc_call('http://' + url_service + ':9002', 'learn_task', params)
    return response


def stop_learn(url_learner):
    rpc_call('http://' + url_learner + ':9002', 'stop_learn')


def short_teach_insertion(hostname, object, hole):
    rpc_call("http://" + hostname + ":8383", "grasp_object",
             {"object": "none", "width": 0., "speed": 0.05, "force": 60., "check_width": False})
    rpc_call("http://" + hostname + ":8383", "teach_object", {"object": object, "teach_width": True,
                                                              "reference_frame": "none", "is_reference_frame": False})
    rpc_call("http://" + hostname + ":8383", "release_object", {"width": 0.05, "speed": 0.2})
    rpc_call("http://" + hostname + ":8383", "grasp_object", {"object": object,"width":0.,"speed":0.05,"force":60.,"check_width":False})
    rpc_call("http://" + hostname + ":8383", "teach_object", {"object": hole, "teach_width": False,
                                                              "reference_frame": "none", "is_reference_frame": False})
    rpc_call("http://" + hostname + ":8383", "release_object",{"width":0.05,"speed":0.2})


async def ws_send(hostname, request):
    uri = "ws://" + hostname + ":8383/mios"
    async with websockets.connect(uri) as websocket:


        message = json.dumps(request)
        await websocket.send(message)
        response = await websocket.recv()
        print(response)
        return json.loads(response)


def start_task_ws(hostname, task):
    request = {
        "method": "start_task",
        "request": {
            "task": task,
            "parameters": {},
            "queue": False
        }
    }
    return asyncio.get_event_loop().run_until_complete(ws_send(hostname, request))


def stop_task_ws(hostname):
    request = {
        "method": "stop_task",
        "request": {
            "nominal": True,
            "success": False,
            "recover": False,
            "empty_queue": False,
            "cost_suc": 0.0,
            "cost_err": 0.0
        }
    }
    return asyncio.get_event_loop().run_until_complete(ws_send(hostname, request))


def wait_for_task_ws(hostname, task_uuid):
    request = {
        "method": "wait_for_task",
        "request": {
            "task_uuid": task_uuid
        }
    }
    return asyncio.get_event_loop().run_until_complete(ws_send(hostname, request))


def start_task_and_wait_ws(hostname, task):
    response = start_task_ws(hostname, task)
    response = wait_for_task_ws(hostname, response["result"]["task_uuid"])
    return response