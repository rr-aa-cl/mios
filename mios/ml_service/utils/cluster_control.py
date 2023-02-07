from xmlrpc.client import ServerProxy
from utils.udp_client import call_method
from typing import Iterable


def stop_ml_services(services: Iterable):
    for s in services:
        proxy = ServerProxy("http://" + s + ":8000")
        proxy.stop_service()
