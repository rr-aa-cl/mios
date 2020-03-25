#!/usr/bin/python3 -u
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from jsonrpc import JSONRPCResponseManager, dispatcher

from threading import Thread


def init():
    run_simple('0.0.0.0', 9005, start_server)


@Request.application
def start_server(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


@dispatcher.add_method
def start_task(**kwargs):
    print(kwargs)

    result = {

    }

    return 0