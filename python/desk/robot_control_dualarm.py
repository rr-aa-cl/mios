#!/usr/bin/env python3

from xmlrpc.server import SimpleXMLRPCServer
import desk_client

r_left = "192.168.3.100"
r_right = "192.168.4.100"
user_name = "franka"
user_password = "frankaRSI"
listening_port = 8008


class robot_control_server():
    def __init__(self):
        self.rpc_server = SimpleXMLRPCServer(("0.0.0.0", listening_port), allow_none=True)
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.reboot_robots, "reboot_robots")

        self.rpc_server.register_function(self.reboot_robots, "reboot_left")
        self.rpc_server.register_function(self.reboot_robots, "reboot_right")
        
    def start(self):
        self.rpc_server.serve_forever()

    def _reboot(self, robot_ip):
        desk_client.reboot(robot_ip, user_name, user_password,"miosL")
    
    def reboot_robots(self):
        self._reboot(r_left)
        self._reboot(r_right)
    
    def reboot_left(self):
        self._reboot(r_left)

    def reboot_right(self):
        self._reboot(r_right)

if __name__ == "__main__":
    s = robot_control_server()
    s.start()

        