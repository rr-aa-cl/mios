from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
from xmlrpc.client import ServerProxy
from threading import Thread
from utils.ws_client import *
import keyboard

class InterfaceServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class EventServer:
    def __init__(self):
        self.rpc_server = InterfaceServer(("0.0.0.0", 8000), allow_none=True)

        self.online = False
        self.subscriber = dict()

    def start_rpc_server(self):
        print("EventServer: Starting RPC server...")
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.subscribe_to_event, "subscribe_to_event")
        self.rpc_server.register_function(self.unsubscribe_from_event, "unsubscribe_from_event")
        self.online = True
        t = Thread(target=self.watchdog)
        t.start()
        self.rpc_server.serve_forever()

    def subscribe_to_event(self, event, sender_ip, sender_port):
        print("EventServer: Subscribing to event " + event)
        if event not in self.subscriber:
            self.subscriber[event] = []
        if (sender_ip, sender_port) not in self.subscriber[event]:
            self.subscriber[event].append((sender_ip, sender_port))

    def unsubscribe_from_event(self, event, sender_ip, sender_port):
        print("EventServer: Unsubscribing from event " + event)
        if event in self.subscriber:
            if (sender_ip, sender_port) in self.subscriber[event]:
                self.subscriber[event].remove((sender_ip, sender_port))

    def trigger_event(self, event, content):
        print("EventServer: Triggering event " + event)
        if event not in self.subscriber:
            return
        for sender in self.subscriber[event]:
            call_method(sender[0], sender[1], "post_event", {"name": event, "content": content})

    def watchdog(self):
        # Implement here any hardware-related stuff -> use trigger_event to notify any subscribers
        button_flag = False
        button_pressed = False
        while self.online is True:
            if keyboard.is_pressed("Enter") is True and button_pressed is False:
                button_pressed = True
            if keyboard.is_pressed("Enter") is False and button_pressed is True:
                button_pressed = False

            if button_pressed is True and button_flag is False:
                self.trigger_event("button_press", {"button_state": True})
                button_flag = True
            elif button_flag is True and button_pressed is False:
                self.trigger_event("button_press", {"button_state": False})
                button_flag = False
            pass
        pass


if __name__ == "__main__":
    server = EventServer()
    server.start_rpc_server()
