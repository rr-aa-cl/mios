import utils.ws_global_loop
import threading
from mongodb_client.mongodb_client import MongoDBClient
from problem_definition.problem_definition import ProblemDefinition
from collective_manager.learning_config import LearningConfig
from utils.helper_functions import *
from run_experiments import *
from threading import Thread
import ipaddress
import subprocess
from queue import PriorityQueue
from xmlrpc.client import ServerProxy,Fault
from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import socket
import logging
import time
from copy import deepcopy
import pprint
import http.client

import fcntl
import struct

def get_interface_ip(ifname: str) -> str | None:
    """
    Gets the IP address of a given network interface.

    Args:
        ifname: The name of the network interface (e.g., 'eth0', 'en0').

    Returns:
        The IPv4 address as a string, or None if not found.
    """
    try:
        # Create a socket object to use for the ioctl call
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Make an ioctl call to get the IP address.
        # SIOCGIFADDR is the request code to get the address.
        # We pack the interface name into a bytes structure.
        packed_addr = fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24]
        
        # The IP address is returned as 4 bytes, so we use inet_ntoa
        # to convert it to the standard dot-decimal string format.
        return socket.inet_ntoa(packed_addr)
    except OSError:
        # This can happen if the interface doesn't exist or has no IP address
        return None
    finally:
        s.close()

PI = 3.141592653
INIT_q = [0, -3.141592653/4, 0, -3 * PI/4, 0, PI/2, PI/4]
MAIN_EVENT_LOOP = None

class InterfaceServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

logger = logging.getLogger("collective_manager")


class CollectiveModule:
    def __init__(self, hostname,connected_robots={},rpc_port=8010):
        global MAIN_EVENT_LOOP
        MAIN_EVENT_LOOP = asyncio.get_event_loop()
        loop_thread = Thread(target=MAIN_EVENT_LOOP.run_forever, daemon=True, name="websocket_main_loop")
        ip_object = False
        try:   # get hostname from IP
            ip_object = ipaddress.ip_address(hostname)
            result = subprocess.run(["avahi-resolve", "-a", str(ip_object)], stdout=subprocess.PIPE,check=True,text=True,shell=False).stdout
            hostname = result[result.find("\t")+1:result.find("\n")]
        except ValueError:
            self.hostname = hostname
        if hostname[-6:] == ".local":
            hostname = hostname[:-6]
        if hostname[-14:] != ".rsi.ei.tum.de":
            self.hostname = hostname + ".rsi.ei.tum.de"
        self.ip = None
        if ip_object:
            self.ip = str(ip_object)
        else:
            try:
                self.ip = socket.gethostbyname(hostname)
            except socket.gaierror:
                logger.error("Module is not listed in the DNS yet.")
                self.ip = get_interface_ip("enp4s0")
        self.wallmount = True
        if self.hostname == "collective-041.rsi.ei.tum.de":
            self.wallmount = False
        logger.debug("Created CollectiveModule on "+str(self.hostname)+" with IP "+str(self.ip))
        self.robot_info_default = {
            "mios_port":None,
            "mongo_port":None,
            "mls_port":None,
            "current_task":"no Information",
            "mios_status":"no Information",  # possible: "no Information", "not running", "Idle", "Reflex", "UserStopped"
            "grasped_object":"no Information",
            "mls_status":"no Information",  # possible: "no Information", "not running", "running", "busy"
            "current_problem_uuid":None,
            "connectivity":"no Information",
            "alert": False,
            "learning_config":None,   # learning configuration for current problem
            "learning_sequence":[],   # list of learning configurations
            "current_camera_position":"no Information",  # number of current camera position (from left to right in robot view)
            #"available_objects": [],  #best case in the same order as mounted from left to right (robot view)
            "time": None,
            "camera_positions":{},  #{"<object>":<position_number>}  so there can be more objects at the same position
            "learning_started":False,
            "waiting_to_start":False,
            "current_experiment": "maintenance",
            "preconditions_fullfilled":False,
            "reseted":False,
            "skip_current_task":False
        }    
        self.connected_robots = connected_robots
        if "left" in self.connected_robots:
            self.connected_robots["left"] = deepcopy(self.robot_info_default)
            self.connected_robots["left"]["mios_port"] = 12000
            self.connected_robots["left"]["mongo_port"] = 27017
            self.connected_robots["left"]["mls_port"] = 8000
            if self.ip:
                self.connected_robots["left"]["mls"] = ServerProxy("http://"+self.ip+":"+str(self.connected_robots["left"]["mls_port"]),allow_none=True)
                self.connected_robots["left"]["mongo"] = MongoDBClient(self.ip,self.connected_robots["left"]["mongo_port"])
            
        if "right" in self.connected_robots:
            self.connected_robots["right"] = deepcopy(self.robot_info_default)
            self.connected_robots["right"]["mios_port"] = 13000
            self.connected_robots["right"]["mongo_port"] = 27017
            self.connected_robots["right"]["mls_port"] = 9000
            if self.ip:
                self.connected_robots["right"]["mls"] = ServerProxy("http://"+self.ip+":"+str(self.connected_robots["right"]["mls_port"]),allow_none=True)
                self.connected_robots["right"]["mongo"] = MongoDBClient(self.ip,self.connected_robots["right"]["mongo_port"])
        self.keep_monitoring = {}
        self.monitoring_threads = None
        self.data_thread = None
        self.last_update = 0
        self.rpc_port = rpc_port
        self.monitoring_data_id = "INVALID"
        for arm in self.connected_robots.keys():
            self.check_database(arm)
        logger.debug("connected_robots: \n"+ pprint.pformat(self.connected_robots,indent=4))
        self.rpc_server = InterfaceServer(("0.0.0.0", self.rpc_port), allow_none=True, logRequests=False)
    
    def check_database(self, arm):
        logger.debug("Check database for "+arm+" arm.")
        collection = "current_state_"+arm
        states = self.connected_robots[arm]["mongo"].read("collective_module",collection,{})
        if not states: # set default if nothing is available
            self.connected_robots[arm]["mongo"].write("collective_module",collection,{"name":"camera","current_camera_position":"no Information", "camera_positions":{}})
        logger.debug("current state: "+str(states))
        set_default_camera = True
        for state in states:  #check states
            if state["name"] == "camera":
                set_default_camera = False
                if "current_camera_position" not in state:
                    self.connected_robots[arm]["mongo"].update("collective_module",collection,{"name":"camera"},{"current_camera_position":"no Information"})
                else:
                    logger.debug("set current_camera_position: "+str(state["current_camera_position"]))
                    self.connected_robots[arm]["current_camera_position"] = state["current_camera_position"]
                if "camera_positions" not in state:
                    self.connected_robots[arm]["mongo"].update("collective_module",collection,{"name":"camera"},{"camera_positions":{}})
                else:
                    logger.debug("set camera_positions: "+str(state["camera_positions"]))
                    self.connected_robots[arm]["camera_positions"] = state["camera_positions"]
        if set_default_camera:
            self.connected_robots[arm]["mongo"].write("collective_module",collection,{"name":"camera","current_camera_position":"no Information", "camera_positions":{}})
                
    
    def get_current_camera_position(self,arm):
        collection = "current_state_"+arm
        camera_state = self.connected_robots[arm]["mongo"].read("collective_module",collection,{"name":"camera"})
        if not camera_state:
            return "no Information"
        else:
            camera_state = camera_state[0]
        if "current_camera_position" in camera_state:
            self.connected_robots[arm]["current_camera_position"] = camera_state["current_camera_position"]
        else:
            return False
        if "camera_positions" in camera_state:
            self.connected_robots[arm]["camera_positions"] = camera_state["camera_positions"]
        
        return camera_state["current_camera_position"]
    
    def store_current_camera_position(self, arm):
        collection = "current_state_"+arm
        self.connected_robots[arm]["mongo"].update("collective_module",collection,{"name":"camera"},{"current_camera_position":self.connected_robots[arm]["current_camera_position"]})

    def set_available_objects(self, objs:dict, arm):
        '''
        objs: dict with available objects as key and camera position as values
        '''
        logger.debug("set_camera_positions to "+str(objs))
        self.connected_robots[arm]["reseted"]=False
        collection = "current_state_"+arm
        #self.connected_robots[arm]["available_objects"] = list(objs.keys())
        self.connected_robots[arm]["camera_positions"] = objs
        self.connected_robots[arm]["mongo"].update("collective_module",collection,{"name":"camera"},{"camera_positions":self.connected_robots[arm]["camera_positions"]})
        return True

    def start_rpc_server(self):
        logger.debug("Collectiveodule started on port "+str(self.rpc_port))
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.check_connectivity, "check_connectivity")
        self.rpc_server.register_function(self.check_mios_state, "check_mios_state")
        self.rpc_server.register_function(self.check_mls, "check_mls")
        self.rpc_server.register_function(self.is_busy, "is_busy")
        self.rpc_server.register_function(self.move_camera, "move_camera")
        self.rpc_server.register_function(self.update_state, "get_state")
        self.rpc_server.register_function(self.add_learning_config, "add_learning_config")
        self.rpc_server.register_function(self.ready_to_learn, "ready_to_learn")
        self.rpc_server.register_function(self.reset_camera, "reset_camera")
        self.rpc_server.register_function(self.start_monitoring, "start_monitoring")
        self.rpc_server.register_function(self.stop_monitoring, "stop_monitoring")
        self.rpc_server.register_function(self.start_learning, "start_learning")
        self.rpc_server.register_function(self.check_pose, "check_pose")
        self.rpc_server.register_function(self.get_connected_robots, "get_connected_robots")
        self.rpc_server.register_function(self.set_available_objects, "set_available_objects")
        self.rpc_server.register_function(self.reset, "reset")
        self.rpc_server.register_function(self.finished,"finished")
        self.rpc_server.register_function(self.is_reseted,"is_reseted")
        self.rpc_server.register_function(self.preconditions_fullfilled,"preconditions_fullfilled")
        self.rpc_server.register_function(self.skip_current_task, "skip_current_task")
        self.rpc_server.register_function(self.get_arms, "get_arms")
        self.rpc_server.register_function(self.reset_alert, "reset_alert")
        self.rpc_server.serve_forever()
        logger.debug("CollectiveModule stopped")

    def reset_alert(self,arm):
        self.connected_robots[arm]["alert"] = False

    def get_arms(self):
        return list(self.connected_robots.keys())
    
    def skip_current_task(self,arm):
        self.connected_robots[arm]["skip_current_task"] = True

    def preconditions_fullfilled(self, arm, insertable):
        if self.connected_robots[arm]["grasped_object"] != insertable:
            return False
        if insertable not in self.connected_robots[arm]["learning_config"].pd.tags:
            logger.debug(f"preconditions_fullfilled: {insertable} not in learning_config")
            return False
        return self.connected_robots[arm]["preconditions_fullfilled"]
    
    def get_gripper_state(self,arm):
        call_method(self.ip,self.connected_robots[arm]["mios_port"],"move_gripper",{"width":0,"speed":1,"force":1})
        try:
            if call_method(self.ip,self.connected_robots[arm]["mios_port"],"get_state")["result"]["gripper_width"] > 0.001:
                return False
        except KeyError:
            return False
        call_method(self.ip,self.connected_robots[arm]["mios_port"],"move_gripper",{"width":1,"speed":1,"force":1})
        try:
            if call_method(self.ip,self.connected_robots[arm]["mios_port"],"get_state")["result"]["gripper_width"] < 0.075:
                return False
        except KeyError:
            return False
        return True
        
    
    def reset(self,stop_monitoring=True):
        logger.debug("+++reset module+++")
        if sum([r["reseted"] for r in self.connected_robots.values()]) == len(self.connected_robots):
            return True
        for robot_info in self.connected_robots.values():
            robot_info["reseted"] = False
        if stop_monitoring:
            self.stop_monitoring()
        for arm, robot in self.connected_robots.items():
            try:
                robot["mls"].stop_service()
            except ConnectionRefusedError:
                logger.error("reset(): ml_service is not running: ConnectionRefusedError")
                
            while robot["mls"].is_busy():
                logger.debug("wait while learning service is stopping...")
                time.sleep(5)
            self.connected_robots[arm]["learning_started"] = False
            self.connected_robots[arm]["current_problem_uuid"] = None
            self.connected_robots[arm]["current_experiment"] = "maintenance/"
            if self.wallmount:
                if not self.move_cart("EndEffector",arm,offset=[-0.15,0,0],context="Move the away from any obstacles",repeat=1,folder="maintenance/",name="reset_MoveUp"):
                    logger.error("Couldn't move the robot 15cm up.")
            else:
                if not self.move_cart("EndEffector",arm,offset=[0,0,-0.15],context="Move the away from any obstacles",repeat=1,folder="maintenance/",name="reset_MoveUp"):
                    logger.error("Couldn't move the robot 15cm up.")
            self.update_state()
            if robot["grasped_object"] != "no Information":
                self.place_insertable(robot["grasped_object"],arm)
            robot["learning_config"] = None
            robot["learning_sequence"] = []
            robot["alert"] = False
            call_method(self.ip,robot["mios_port"],"release_object")

            self.move("default",arm, speed=True,context="Move to pose above the experiment in order to avoid joint limits and obstacles.",folder=robot["current_experiment"],name="reset_default")  # self.ip,"default",port=robot["mios_port"],log_name=, context=,folder=)   # enter experiment description as logname/foldername
            call_method(self.ip,robot["mios_port"],"home_gripper")
            while not self.get_gripper_state(arm):
                call_method(self.ip,robot["mios_port"],"home_gripper")
            self.connected_robots[arm]["reseted"] = True
        logger.debug("+++reset done+++")
        
        return True
    
    def is_reseted(self,arm):
        return self.connected_robots[arm]["reseted"]

    def stop_rpc_server(self):
        logger.debug("stop_rpc_server()")
        self.rpc_server.server_close()
        self.rpc_server.shutdown()
        logger.debug("stop_rpc_server.end")
        
    def _get_ipv4_by_hostname(self, hostname):
        try:
            ips = list(
                i        # raw socket structure
                    [4]  # internet protocol info
                    [0]  # address
                for i in 
                socket.getaddrinfo(
                    hostname,
                    0  # port, required
                )
                if i[0] is socket.AddressFamily.AF_INET  # ipv4

                # ignore duplicate addresses with other socket types
                and i[1] is socket.SocketKind.SOCK_RAW  
            )
        except socket.gaierror:
            logger.debug("host "+self.hostname+" is not listed in the DNSserver")
            return False
        self.ip = ips[0]  # store only single ip
        return ips[0]

    def _ping(self):
        if self.ip:
            hostname = self.ip
        else:
            hostname = self.hostname
        # response = os.system(f"ping -c 1 -w 1 {hostname} &> /dev/null")  #  1 ping with max duration of 1 second
        response = subprocess.run(['ping', '-c', '1', '-W', '1', hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #^change this line to subprocess.run()^
        if response.returncode != 0:
            logger.error("host "+self.hostname+" is not pingable")
            return False
        else:
            return True

    def check_connectivity(self):
        if not self.ip:  # ask the DNS server
            if not self._get_ipv4_by_hostname(self.hostname):
                self.connectivity = "not connected"
                return False  # no DNS entry
        if not self._ping():  # ping the module
            self.connectivity = "not pingable"
            return False  # not pingable
        self.connectivity = "connected"
        return True
    
    def check_mios_state(self):
        if not self.ip:
            robot = self.hostname
        else:
            robot = self.ip
        for robot_info in self.connected_robots.values():
            response_mios = call_method(robot, robot_info["mios_port"],"get_state",timeout=1)    
            if not response_mios:
                robot_info["mios_status"] = "not running"
                robot_info["grasped_object"]= "no Information"
                robot_info["current_task"] = "no Information"
                logger.error("mios on host "+self.hostname+" is not running on port"+str(robot_info["mios_port"]))   
            else:
                robot_info["grasped_object"] = response_mios["result"]["grasped_object"]
                robot_info["current_task"] = response_mios["result"]["current_task"]
                if "status" in response_mios["result"]:
                    robot_info["mios_status"] = response_mios["result"]["status"]
                else:
                    if response_mios["result"]["current_task"] == "IdleTask":
                        robot_info["mios_status"] = "Reflex"
                    else:
                        robot_info["mios_status"] = "Idle"
        return True
    
    def check_mls(self) -> dict:
        result = {}
        for arm, robot_info in self.connected_robots.items():
            if not robot_info["mls"]:
                robot_info["mls"] = ServerProxy("http://"+self.ip+":"+str(robot_info["mls_port"]),allow_none=True)
            try:
                busy = robot_info["mls"].is_busy()
            except ConnectionRefusedError:
                robot_info["mls_status"] = "not running"
                logger.error("ml_service on host "+self.hostname+":"+str(robot_info["mls_port"])+" - "+arm+" is not reachable.")
                result[arm] = False
                continue
            except http.client.CannotSendRequest:
                robot_info["mls_status"] = "not running"
                logger.error("ml_service on host "+self.hostname+":"+str(robot_info["mls_port"])+" - "+arm+" is not running.")
                result[arm] = False
                continue
            
            robot_info["mls_status"] = "running"
            if busy:
                logger.debug("ml_service on host "+self.hostname+":"+str(robot_info["mls_port"])+" is busy.")
                robot_info["mls_status"] = "busy"
            result[arm] = robot_info["mls_status"]
        return result
    
    def is_busy(self,arm):
        if not self.check_mls()[arm]:
            return True
        self.check_mios_state()
        if self.connected_robots[arm]["current_task"] != "IdleTask":
            return True
        return False
        
    def get_connected_robots(self):
        return self.connected_robots
    
    def get_state(self):
        state = {   "hostname":self.hostname,
                    "ip":self.ip,
                    "time_epoch": time.time(),
                    "time": time.strftime("%Y-%m-%d  %H:%M:%S", time.localtime())
                }
        for arm,robot_info in self.connected_robots.items():
            state[arm] = {}
            for k, value in robot_info.items():
                if k == "mls" or k=="mongo" or k=="learning_config" or k=="learning_sequence" or k=="camera_positions":
                    continue
                state[arm][k] = deepcopy(value)
            if robot_info["learning_config"]:
                state[arm]["learning_config"] = robot_info["learning_config"].to_dict()
            else:
                state[arm]["learning_config"] = None
            state[arm]["learning_sequence"] = []
            for lc in robot_info["learning_sequence"]:
                state[arm]["learning_sequence"].append(str(lc.name)+": "+str(lc.pd.skill_instance))
        
        return state

    def update_state(self):
        if time.time() - self.last_update < 5:
            return self.get_state()
        #logger.debug("update state")
        self.last_update = time.time()
        for arm, robot_info in self.connected_robots.items():
            # robot_info = deepcopy(self.robot_info_default)
            if not self.connected_robots[arm]["camera_positions"]:
                logger.debug("load camera positions from database")
                collection = "current_state_"+arm
                camera_state = self.connected_robots[arm]["mongo"].read("collective_module",collection,{"name":"camera"})
                if camera_state:
                    camera_state = camera_state[0]
                    if "current_camera_position" in camera_state:
                        logger.debug("set current camera position: "+str(camera_state["current_camera_position"]))
                        self.connected_robots[arm]["current_camera_position"] = camera_state["current_camera_position"]
                    if "camera_positions" in camera_state:
                        logger.debug("set camera_positions: "+str(camera_state["camera_positions"]))
                        self.connected_robots[arm]["camera_positions"] = camera_state["camera_positions"]
                else:
                    logger.error("Cannot find find camera state at database")
                
                
        self.connectivity = "no Information"
        if not self.check_connectivity():
            return self.get_state()
        if not self.check_mios_state():
            return self.get_state()
        self.check_mls()
        return self.get_state()
    
    def raise_hand(self, arm = "left"):
        logger.error("raise hand")
        self.connected_robots[arm]["reseted"]=False
        if self.connected_robots[arm]["alert"]:
            return True
        self.connected_robots[arm]["alert"] = True
        if not self.move("raise_hand",arm,folder=self.connected_robots[arm]["current_experiment"],name="raise_hand"):
            return False
        return True
    
    def move(self, pose, arm, speed=False,context="",folder="", name="MoveJoint", repeat=3,log=True):
        logger.debug("joint move to "+pose)
        count = 0
        result = False
        result_info="no result"
        while not result:
            if count>0:
                if self.wallmount:
                    self.move_cart("EndEffector",arm,speed=False, offset=[-0.15,0,0],log=False)
                else:
                    self.move_cart("EndEffector",arm,speed=False, offset=[0,0,0.15],log=False)
            if count > repeat:
                logger.error("not able to move to JointPose "+pose+": "+str(result_info))
                return False
            try:
                result_info = move_joint(self.ip, pose, wait=True,port=self.connected_robots[arm]["mios_port"],speed=speed,context=context,folder=folder,log_name=name,logging=log)
                result = result_info["result"]["task_result"]["success"]
            except (KeyError, TypeError) as e:
                logger.error("KeyError/TypeError when trying to move: ",result_info, " ERROR:",e)
                pass
            count += 1
        return True
    
    def move_cart(self, pose, arm, speed=False, offset=[0,0,0],context="",folder="",name="MoveCart",repeat=3,log=True):
        logger.debug("cart move to "+pose)
        count = 0
        result = False
        result_info="no result"
        while not result:
            if count > repeat:
                logger.error("Cartesian movement to "+pose+" not successfull: "+str(result_info))
                return False
            result_info = move(self.ip, pose, wait=True,port=self.connected_robots[arm]["mios_port"],speed=speed,offset=offset, context=context,folder=folder,log_name=name,logging=log)
            try:
                result = result_info["result"]["task_result"]["success"]
            except (KeyError, TypeError) as e:
                logger.error("KeyError/TypeError when trying to move: ",result_info, " ERROR:",e)
                result = False
                pass
            count += 1
        return True
    
    def reset_camera(self,arm):
        logger.debug("reset_camera")
        self.connected_robots[arm]["current_camera_position"] = "no Information"
        if not self.move("default",arm,speed=True, context="Move to pose above the experiment in order to avoid joint limits and obstacles.",folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="reset_default"):
            logger.error("Cannot move to default position")
            return False
        #call_method(self.ip, self.connected_robots[arm]["mios_port"],"home_gripper")
        call_method(self.ip, self.connected_robots[arm]["mios_port"],"move_gripper",{"width":0,"speed":1,"force":1,"epsilon_outer":1})
        
        max_pos = max(self.connected_robots[arm]["camera_positions"].values())
        min_pos = min(self.connected_robots[arm]["camera_positions"].values())

        if not self.move("camera_"+str(max_pos)+"_right_above",arm,speed=True, 
                         context="Goal is to move the camera to face the first object, but the current camera position is unknown. " \
                         "Move above the camera position of the last object available",
                         folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(max_pos)+"_JointMoveAbove"):
            return False
        if not self.move("camera_"+str(max_pos)+"_right",arm,speed=False, 
                              context = "Goal is to move the camera to face the first object, but the current camera position is unknown. " \
                              "Engage with the camera at the camera position of the last object available.",
                              folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(max_pos)+"_JointMoveContact"):
            return False
        for pos in sorted(self.connected_robots[arm]["camera_positions"].values(), reverse=True):
            call_method(self.ip, self.connected_robots[arm]["mios_port"],"move_gripper",{"width":0,"speed":1,"force":1,"epsilon_outer":1})
            if pos == max_pos:
                continue
            if not self.move_cart("camera_"+str(pos)+"_right",arm,speed=False, 
                                  context = "Goal is to move the camera to face the first object, " \
                                  "but the current camera position is unknown. Move the camera to the next object on the left side.",
                                  folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(pos)+"_MoveCart"):
                self.connected_robots[arm]["current_camera_position"] = "no Information"
                self.store_current_camera_position(arm)
                return False
            self.connected_robots[arm]["current_camera_position"] = pos
            #if not self.move_cart("camera_"+str(pos)+"_right_above",arm,speed=False):
            #    return False
            #if not self.move("default",arm,speed=False):
            #    return False
            if pos == min_pos:
                break
            #if not self.move_cart("camera_"+str(pos)+"_right_above",arm,speed=True):
            #    return False
            #if not self.move("camera_"+str(pos)+"_right",arm,speed=True):
            #    return False
        self.connected_robots[arm]["current_camera_position"] = min_pos
        self.store_current_camera_position(arm)
        logger.debug("reset_camera successful")
        if self.wallmount:
            self.move_cart("EndEffector",arm,False,offset=[-0.15,0,0.03],context="Move up the EndEffector in order to avoid obstacles during further movements.",
                       folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="retract")
        else:
            self.move_cart("EndEffector",arm,False,offset=[0.03,0,0.15],context="Move up the EndEffector in order to avoid obstacles during further movements.",
                       folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="retract")
        
        return True

    def move_camera(self, pos, arm):
        '''
        pos is index of available object
        arm is eather left of right
        '''
        
        self.connected_robots[arm]["reseted"]=False
        grasped_object = self.connected_robots[arm]["grasped_object"]

        if type(self.connected_robots[arm]["current_camera_position"]) is not int:
            logger.warning("current camera position not known. Asking database...")
            if type(self.get_current_camera_position(arm)) is not int:  #this also updates the camera_positions stored
                logger.warning("current camera position still not known. resetting...")
                if not self.reset_camera(arm):
                    logger.error("Cannot reset camera. Position unknown.")
                    return False
                
        if pos not in self.connected_robots[arm]["camera_positions"].values():
            logger.error("Position "+str(pos)+" not available on "+self.hostname+" - "+arm)
            return False
        

        current_position = self.connected_robots[arm]["current_camera_position"]
        if type(current_position) is not int:
            logger.error("Cannot Position unknown. Cannot move camera.")
            return False
        if current_position == pos:
            self.store_current_camera_position(arm)
            return True
        
        
        if grasped_object == "NullObject" or grasped_object == "no Information":
            pass
        else:
            logger.debug("move camera to position "+str(pos)+". Place "+grasped_object+" before.")
            self.place_insertable(grasped_object,arm)

        if not self.move("default",arm,speed=True,context="Move to pose above the experiment in order to avoid joint limits and obstacles.",
                         folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="default"):
            logger.error("Not able to move to "+"default"+" on "+self.hostname+" - "+arm)
            return False
        call_method(self.ip,self.connected_robots[arm]["mios_port"],"home_gripper")
        call_method(self.ip, self.connected_robots[arm]["mios_port"],"move_gripper",{"width":0,"speed":1,"force":1,"epsilon_outer":1})
        logger.debug("move camera to position "+str(pos))
        if current_position>pos:
            #move camera left

            while(current_position != pos):
                call_method(self.ip, self.connected_robots[arm]["mios_port"],"move_gripper",{"width":0,"speed":1,"force":1,"epsilon_outer":1})
                if not self.move("camera_"+str(current_position)+"_right_above",arm,speed=True, 
                             context = "Goal is to move the camera to face the "+str(pos)+". object. "
                             "Current position is"+str(current_position)+". Move the camera above position "+str(current_position)+".",
                             folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(pos)+"_JointMoveAbove"):
                    return False
                if not self.move("camera_"+str(current_position)+"_right",arm,speed=True, 
                                      context = "Goal is to move the camera to face the "+str(pos)+". object. "
                                      "Current position is"+str(current_position)+". Engage with the camera at the camera position "+str(current_position)+".",
                                      folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(pos)+"_JointMoveContact"):
                    return False
                if not self.move_cart("camera_"+str(current_position-1)+"_right",arm,speed=False, 
                                      context = "Goal is to move the camera to face the "+str(pos)+". object. "
                                      "Current position is"+str(current_position)+". Move camera to position "+str(current_position-1)+".",
                                      folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(pos)+"_MoveCart"):
                    self.connected_robots[arm]["current_camera_position"] = "no Information"
                    self.store_current_camera_position(arm)
                    return False
                self.move_cart("camera_"+str(current_position-1)+"_right_above",arm,speed=True,
                               context="Move away from the camera in order to avaoid further camaera disallocations.",
                               folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(pos)+"_retract")
                
                #if not self.move("default",arm,speed=False):
                #    return False
                current_position = current_position - 1
                self.connected_robots[arm]["current_camera_position"] = current_position
                self.store_current_camera_position(arm)
        else:
             #move camera right
            while(current_position != pos):
                call_method(self.ip, self.connected_robots[arm]["mios_port"],"move_gripper",{"width":0,"speed":1,"force":1,"epsilon_outer":1})
                if not self.move("camera_"+str(current_position)+"_left_above",arm,speed=True, 
                                 context = "Goal is to move the camera to face the "+str(pos)+". object. Current position is"+str(current_position)+
                                 ". Move the camera above position "+str(current_position)+" into a joint pose away from joint limits.",
                                 folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(pos)+"_JointMoveAbove"):
                    return False
                if not self.move("camera_"+str(current_position)+"_left",arm,speed=True, 
                                 context = "Goal is to move the camera to face the "+str(pos)+". object. Current position is"+str(current_position)+
                                 ". Engage with the camera at the camera position "+str(current_position)+".",
                                 folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(pos)+"_JointMoveContact"):
                    return False
                if not self.move_cart("camera_"+str(current_position+1)+"_left",arm,speed=False, 
                                      context = "Goal is to move the camera to face the "+str(pos)+". object. Current position is"+str(current_position)+
                                      ". Move camera to position "+str(current_position-1)+".",
                                      folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(pos)+"_MoveCart"):
                    self.connected_robots[arm]["current_camera_position"] = "no Information"
                    self.store_current_camera_position(arm)
                    return False
                
                self.move_cart("camera_"+str(current_position+1)+"_left_above",arm,speed=True, context = "Goal is to move the camera to face the "+str(pos)+
                               ". object. Current position is"+str(current_position+1)+". Move the camera above position "+str(current_position+1)+
                               " to be able to move the robot freely without displacing the camera.",
                               folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="camera"+str(pos)+"_retract")

                #if not self.move("default",arm,speed=False,context="Move to pose above the experiment in order to avoid joint limits and obstacles."):
                #    return False
                current_position = current_position + 1
                self.connected_robots[arm]["current_camera_position"] = current_position
                self.store_current_camera_position(arm)
        if self.wallmount:
            self.move_cart("EndEffector",arm,False,offset=[-0.15,0,0.03],context="Move up the EndEffector in order to avoid obstacles with further movements.",
                       folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="final_retract")
        else:
            self.move_cart("EndEffector",arm,False,offset=[0.03,0,0.15],context="Move up the EndEffector in order to avoid obstacles with further movements.",
                       folder=self.connected_robots[arm]["current_experiment"]+"camera_changing/",name="final_retract")
        return True

    def add_learning_config(self, pd:dict, sc: dict, knowledge:dict, priority:int=0, arm:str="left", experiment_name="anon"):
        '''
        setting the learning config inside here is ment to prevent conflicting task allocations from different experiments running in parallel
        also it is used for logging reasons
        '''
        logger.debug("add learnig config: "+str(pd["tags"])+" with knowledge "+str(knowledge))
        self.connected_robots[arm]["reseted"]=False
        pd_class = ProblemDefinition.from_dict(pd)
        if sc["service_name"] == "cmaes":
            sc_class = CMAESConfiguration()
            sc_class.from_dict(sc)
        elif sc["service_name"] == "svm":
            sc_class = SVMConfiguration()
            sc_class.from_dict(sc)
        elif sc["service_name"] == "origPSP":
            sc_class = OrigPSPConfiguration()
            sc_class.from_dict(sc)
        knowledge_class = Knowledge()
        knowledge_class.from_dict(knowledge)
       
        if arm=="left":
            self.connected_robots["left"]["learning_sequence"].append(LearningConfig(pd=pd_class,sc=sc_class,knowledge=knowledge_class,priority=priority,name=experiment_name))
            logger.debug("added learning config with knowledge: "+str(self.connected_robots["left"]["learning_sequence"][-1].knowledge.mode))
            return True
        if arm=="right":
            self.connected_robots["right"]["learning_sequence"].append(LearningConfig(pd_class,sc_class,knowledge_class,priority=priority,name=experiment_name))
            logger.debug("added learning config with knowledge: "+str(self.connected_robots["right"]["learning_sequence"][-1].knowledge.mode))
            return True
        logger.error("something went wrong with adding learning configs -.- "+arm)
        return False
    
    def ready_to_learn(self, arm): 
        #logger.debug("ready_to_learn()")
        # if not self.connected_robots[arm]["learning_sequence"]:
        #     logger.error("No Learning Configuration found: "+str(self.connected_robots[arm]["learning_sequence"]))
        #     return False
        if not self.connected_robots[arm]["learning_config"]:
            logger.error("No learning config is loaded")
            return False
        self.update_state()
        insertable = self.connected_robots[arm]["learning_config"].pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]
        #print("ready_to_learn: camera_positions: ",self.connected_robots[arm]["camera_positions"], "for ", insertable)
        #if self.connected_robots[arm]["current_camera_position"] != self.connected_robots[arm]["camera_positions"][insertable]:
        #    logger.error("Camera at wrong position. Not ready to learn")
        #    return False
        if not self.connected_robots[arm]["grasped_object"] == insertable:
            logger.error("wrong object grasped. Not ready to learn")
            return False
        if not self.connected_robots[arm]["current_task"] == "IdleTask":
            logger.error("Robot is not ready to learning, because of task execution: "+self.connected_robots[arm]["current_task"])
            return False
        return True

    def change_insertable(self,arm):
        insertable = self.connected_robots[arm]["learning_config"].pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]
        if self.connected_robots[arm]["grasped_object"] == "NullObject":
            logger.debug("change_insertable to "+insertable)
            return self.grasp_insertable(insertable, arm)
        current_object = self.connected_robots[arm]["grasped_object"]
        if current_object == insertable:
            #logger.debug("insertable already grasped: "+insertable)
            return True
        logger.debug("change_insertable to "+insertable)
        if not self.place_insertable(current_object,arm):
            return False
        return self.grasp_insertable(insertable,arm)

    def move_to_approach_pose(self, arm):
        logger.debug(arm+" move_to_approach_pose")
        if not self.connected_robots[arm]["learning_config"]:
            logger.error("No learning config available: Cannot move to approach pose")
            return False
        insertable = self.connected_robots[arm]["learning_config"].pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]
        dist = np.linalg.norm(np.array(self.check_pose(insertable+"_container_approach",arm)["q"]) - 
                              np.array(call_method(self.ip, self.connected_robots[arm]["mios_port"],"get_state")["result"]["q"])
                              )
        if dist<0.05:
            logger.debug("approach pose already reached for "+insertable)
            return True
        if self.ready_to_learn(arm):
            count = 0
            self.move("default",arm,context="Move to a pose above the environment to prepare next steps.",
                             folder=self.connected_robots[arm]["current_experiment"]+"approach/",speed=True,name="default")
            while not self.move(insertable+"_container_above",arm,  # get more information why this isnt working...
                             context="Move to a pose above the next object to be learned. The next object is "+insertable,
                             folder=self.connected_robots[arm]["current_experiment"]+"approach/",speed=True,name=insertable+"_above"):
                logger.error("cannot move to container_above pose after ready to learn.")
                count+=1
                time.sleep(5)
                if count>10:
                    logger.error("stuck at move to approach")
                    return False
            while not self.move(insertable+"_container_approach",arm,
                             context="Move to starting pose for learning the next object. The next object is "+insertable,
                             folder=self.connected_robots[arm]["current_experiment"]+"approach/",speed=True,name=insertable+"_approach"):
                logger.error("cannot move to approach pose after ready to learn.")
                count+=1
                time.sleep(5)
                if count>15:
                     logger.error("stuck at move to approach, move to approach pose specifically")
                return False
        else:
            logger.error("not ready to learn. Check errors above")
            return False
        self.connected_robots[arm]["preconditions_fullfilled"] = True
        logger.info("waiting for start learning command")
        #time.sleep(60) # wait to start learning. 
        return True
    def _get_current_ml_results(self,arm):
        robot_info = self.connected_robots[arm]
        try:
            ml_results = robot_info["mongo"].read("ml_results","insertion",{"meta.uuid":self.connected_robots[arm]["current_problem_uuid"]})[0]
        except IndexError:
            logger.error("monitoring: Cannot find current_problem_uuid ("+str(self.connected_robots[arm]["current_problem_uuid"])+") in ml_results. Something went wrong. Try to search for tags...")
            data = robot_info["mongo"].read("ml_results","insertion",{"meta.tags":robot_info["learning_config"].pd.tags})
            if len(data) < 1:
                logger.error("monitoring: didnt find entry for "+str(robot_info["learning_config"].pd.tags))
                return {}
            if len(data) > 1:
                logger.error("monitoring: found multiples entries for "+str(robot_info["learning_config"].pd.tags)+". Picking latest...")
            ml_results={}
            latest=0
            for d in data:
                if d["meta"]["t_0"] > latest:
                    ml_results = d
        return ml_results
    
    def _run_monitoring(self,arm):
        logger.debug("start_monitoring")
        count = 0
        count_2 = 0
        count_alert=0
        last_time = 0
        state = self.update_state()
        #for arm, robot_info in self.connected_robots.items():  # prepare robot
        robot_info = self.connected_robots[arm]
        logger.debug("learning_sequence for "+arm+": "+str(state[arm]["learning_sequence"]))
        #while not self.move("default", arm, speed=True,context="Move to pose above the experiment table in order to avoid joint limits and obstacles before starting.",folder=self.connected_robots[arm]["current_experiment"],name="start_monitoring_default"):
        #    logger.error("Couldn't move the robot to default joint position -> toggle UserStop or reboot robot")

        #if robot_info["grasped_object"] != "NullObject" and robot_info["grasped_object"] != "no Information":
        #    self.place_insertable(robot_info["grasped_object"], arm)
        #    self.move("default", arm, speed=True, context="Move to pose above the experiment table in order to avoid joint limits and obstacles before starting.",folder=self.connected_robots[arm]["current_experiment"],log=False)
        #call_method(self.ip,robot_info["mios_port"],"home_gripper")

        self.connected_robots[arm]["preconditions_fullfilled"] = False
        grasping_count = 0
        while arm in self.keep_monitoring:
            if time.time() - last_time > 5:
                last_time = time.time()
                self.update_state()
                #for arm, robot_info in self.connected_robots.items():
                if robot_info["mios_status"] == "Reflex":
                    call_method(self.ip,robot_info["mios_port"],"unlock_brakes")
                    if self.connected_robots[arm]["learning_started"]:
                        insertable = robot_info["learning_config"].pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]
                        call_method(self.ip,robot_info["mios_port"],"set_grasped_object",{"object":insertable})
                if self.connected_robots[arm]["alert"]:
                    if count_alert==0:
                        logger.error("ALERT: look at error infomation above ^")
                    count_alert+=1
                    if count_alert>100:
                        count_alert=0
                    continue
                                            
                if robot_info["mls_status"] == "no Information":
                    logger.debug("no information on mls_status")
                    continue
                if self.connected_robots[arm]["learning_started"]:
                    if not robot_info["skip_current_task"]:
                        insertable = robot_info["learning_config"].pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]
                        if robot_info["grasped_object"] != insertable:
                            call_method(self.ip,robot_info["mios_port"],"set_grasped_object",{"object":insertable})
                        if robot_info["mls_status"] == "busy":
                            if count == 0:
                                logger.debug(arm+" mls_status is busy...")
                            if count%100==0:
                                logger.debug(arm+" mls_status is still busy...")
                            count += 1
                            if count == 100 and robot_info["current_problem_uuid"]:
                                ml_results = self._get_current_ml_results(arm)
                                if len(ml_results) < 3:
                                    logger.error("ml service is not producing data")
                                    self.reset(stop_monitoring=False)
                                    self.raise_hand(arm)
                                    logger.error("Module is not learning properly. Check it visually")
                            continue
                    else:
                        logger.info("skipping task: "+robot_info["learning_config"].pd.skill_instance)
                        self.connected_robots[arm]["mls"].stop_service()
                        robot_info["skip_current_task"] = False
                    # if robot_info["learning_config"]:
                    #     if robot_info["mls_status"] == "running" and not robot_info["current_problem_uuid"]:
                    #         if count_2 == 0:
                    #             logger.debug("waiting to start learning obejct "+str(robot_info["learning_config"].pd.skill_instance))
                    #         if count_2 % 10 == 0:
                    #             logger.debug("still waiting to start learning obejct "+str(robot_info["learning_config"].pd.skill_instance))
                    #         continue
                    # else:
                    #     logger.debug("no learning config loaded yet...")
                    if robot_info["current_problem_uuid"]:  # finished but not unloaded
                        ml_results = self._get_current_ml_results(arm)
                        if "final_results" not in ml_results:
                            logger.error("Final results have not been written")
                            continue
                        else:
                            logger.info("learning finished :) " + robot_info["grasped_object"])
                            robot_info["current_problem_uuid"] = None
                            robot_info["learning_started"] = False
                            robot_info["preconditions_fullfilled"] = False
                            self.place_insertable(robot_info["grasped_object"],arm)
                            call_method(self.ip,robot_info["mios_port"],"release_object")
                            robot_info["learning_config"] = None
                            robot_info["current_experiment"] = "maintenance"

                #set next problem:
                state = self.update_state()
                if robot_info["learning_sequence"] and not robot_info["learning_config"]:
                    grasping_count = 0
                    logger.debug("set next learning config: "+str( robot_info["learning_sequence"][0].pd.tags))
                    robot_info["preconditions_fullfilled"] = False
                    robot_info["learning_config"] = robot_info["learning_sequence"].pop(0)
                    robot_info["current_experiment"] = "/".join(robot_info["learning_config"].pd.tags[:3]) + "/"
                    robot_info["learning_config"].pd.add_skill_info = {
                        "log_data": True,
                        "log_name": "/".join(robot_info["learning_config"].pd.tags[:3]) + "/",
                        "log_to_file":True,
                        "meta":{
                            "tags":robot_info["learning_config"].pd.tags,
                            "time":time.time()
                        }
                    }
                if not robot_info["learning_config"]:
                    logger.debug("no learning config and no learning sequence present. Raising arm")
                    self.raise_hand(arm)
                    self.keep_monitoring.pop(arm)
                    continue
                if robot_info["skip_current_task"]:
                    logger.info("skipping task: "+robot_info["learning_config"].pd.skill_instance)
                    robot_info["learning_config"] = None
                    robot_info["preconditions_fullfilled"] = False
                    robot_info["current_experiment"] = "maintenance"
                    robot_info["skip_current_task"] = False
                    continue


                insertable = robot_info["learning_config"].pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]

                # pos = robot_info["camera_positions"][insertable]
                # if not self.move_camera(pos, arm):
                #     logger.error("Cannot move camera to Position "+str(pos))
                #     continue
                if not self.change_insertable(arm):  #grasp objects
                    logger.error("changing insertable to "+str(insertable)+" was unsuccessful. \nSkipping learning_config\n")
                    if grasping_count > 2: 
                        robot_info["learning_config"] = None
                    continue
                grasping_count = 0
                self.move_to_approach_pose(arm)
                robot_info["alert"] = False
                #robot_info["current_problem_uuid"] = self.start_learning(arm)
        logger.debug(f"Monitoring ended for arm {arm}!"+str(self.keep_monitoring))
    
    def place_insertable(self, insertable, arm):
        self.move("default",arm,speed=True,context="Move to pose above the experiment in order to avoid joint limits and obstacles before placing the current insertable.",folder=self.connected_robots[arm]["current_experiment"]+"place_object/",name="default")
        logger.debug("place insertable: "+str(insertable))
        port = self.connected_robots[arm]["mios_port"]
        if insertable == "NullObject" or insertable == "no Information":
            logger.error("Cannot place insertable NullObject")
            return False
        if not place_insertable(self.ip,insertable,insertable+"_box_container",insertable+"_box_container_approach",insertable+"_box_container_above",
                                port=port,folder=self.connected_robots[arm]["current_experiment"]+"place_object/",max_time=1.5*60):
            logger.error("Cannot place Insertable "+insertable)
            return False
        if self.wallmount:
            if not self.move_cart(insertable+"_box_container_above", arm,offset=[-0.05,0,0], 
                              context="Retract to a position above the object container after successfull placeing and releasing the object",
                              folder=self.connected_robots[arm]["current_experiment"]+"place_object/",name="MoveUp"):
                logger.error("Cannot move out of "+insertable+"_box_container after placing insertable")
        else:
            if not self.move_cart(insertable+"_box_container_above", arm,offset=[0,0,0.05], 
                              context="Retract to a position above the object container after successfull placeing and releasing the object",
                              folder=self.connected_robots[arm]["current_experiment"]+"place_object/",name="MoveUp"):
                logger.error("Cannot move out of "+insertable+"_box_container after placing insertable")
        return True
    
    def grasp_insertable(self, insertable,arm):
        self.move("default",arm,speed=True, context="Move to pose above the experiment in order to avoid joint limits and obstacles before placing the current insertable.",folder=self.connected_robots[arm]["current_experiment"]+"grasp_object/",name="default_before")
        logger.debug("grasp insertable: "+str(insertable))
        port = self.connected_robots[arm]["mios_port"]
        if insertable == "NullObject" or insertable == "no Information":
            logger.error("Cannot grasp insertable")
            return False
        if not grasp_insertable(self.ip,insertable,insertable+"_box_container",insertable+"_box_container_approach",insertable+"_box_container_above",
                                port=port,folder=self.connected_robots[arm]["current_experiment"]+"grasp_object/",max_time=3*60):
            logger.error("Cannot grasp insertbale "+insertable)
            return False
        if self.wallmount:
            if not self.move_cart(insertable+"_box_container_above", arm,offset=[-0.0,0,0], context="Retract to a position above the object container after successfull grasping the object",
                                folder=self.connected_robots[arm]["current_experiment"]+"grasp_object/",name="retract"):
                logger.error("Cannot move out of "+insertable+"_box_container after grasping insertable.")
        else:
            if not self.move_cart(insertable+"_box_container_above", arm,offset=[-0.0,0,0], context="Retract to a position above the object container after successfull grasping the object",
                              folder=self.connected_robots[arm]["current_experiment"]+"grasp_object/",name="retract"):
                logger.error("Cannot move out of "+insertable+"_box_container after grasping insertable.")
        self.move("default",arm,speed=True, context="Move to pose above the experiment in order to prepare for further movements.",folder=self.connected_robots[arm]["current_experiment"]+"grasp_object/",name="default_after")
        return True

    def _data_storing(self, mongo_id:str):
        last_time = 0
        while self.keep_monitoring:  # while arm in self.keep_monitoring
            if time.time() - last_time > 60:
                state = self.update_state()
                self.global_db.update("modules", self.hostname,{"_id": mongo_id},{str(int(state["time_epoch"])): state})
                last_time = time.time()
        
    def check_tags_unused(self, tags:list[str]):
        mongodb_client = MongoDBClient(self.ip)
        data = mongodb_client.read("ml_results","insertion",{"meta.tags":tags})
        if len(data) > 0:
            return False
        return True
    
    def start_monitoring(self, global_db_ip, experiment_name:str = "INVALID",tags=[]):
        logger.debug("commanded to start monitoring")
        arms = self.connected_robots.keys()
        start_data_stread = True
        for robot_info in self.connected_robots.values():
            robot_info["reseted"]=False
        not_running = list(arms)
        if self.monitoring_threads is not None:
            for t in self.monitoring_threads:
                if t.name[11:] in not_running and t.is_alive():
                    logger.error(f"monitoring threads {str(t.name)} are already running.")
                    not_running.pop(not_running.index(t.name[11:]))
            #arms = not_running
        if self.data_thread is not None:
            if self.data_thread.is_alive():
                start_data_stread = False
                logger.error(f"data threads {str(t.name)} are already running.")
        self.keep_monitoring = {arm:True for arm in arms}
        self.update_state()
        self.global_db = MongoDBClient(global_db_ip)
        state = self.get_state()
        self.monitoring_threads = []
        for arm in not_running:
            self.monitoring_threads.append(Thread(target=self._run_monitoring, args=(arm,),name="monitoring_"+str(arm)))
            self.monitoring_threads[-1].start()
        if start_data_stread:
            mongo_id = self.global_db.write("modules",self.hostname, {"meta":{"experiment":experiment_name, "tags":tags}, str(state["time_epoch"]): state})
            self.data_thread = Thread(target=self._data_storing, args=(mongo_id, ), name="data_storing",daemon=True)
            self.data_thread.start()
            self.monitoring_data_id = mongo_id
        logger.debug(f"start_monitoring: {str(self.keep_monitoring)}, started data thread: {start_data_stread}, started monitoring thread: {not_running}")
        return self.monitoring_data_id

    def stop_monitoring(self):
        logger.debug("Stop monitoring")
        self.keep_monitoring = {}
        if self.monitoring_threads is not None:
            for monitoring_thread in self.monitoring_threads:
                if monitoring_thread is not None:
                    monitoring_thread.join()
            self.monitoring_threads = None
        if self.data_thread is not None:
            self.data_thread.join()
            self.data_thread = None

    def start_learning(self,arm):
        '''
        uuid for learning pipeline (get when larning problem is appended to learning pipeline)
        '''
        print("start_learning-1")
        if self.connected_robots[arm]["current_problem_uuid"] is not None:  
            logger.debug(f"A uuid for this arm ({arm})is already set")
            time.sleep(2)
            if self.connected_robots[arm]["learning_started"]:
                return self.connected_robots[arm]["current_problem_uuid"]  # already started by other collective_manager
            else:
                logger.error("learning uuid was set, but learning wasnt started?")
                return self.connected_robots[arm]["current_problem_uuid"]
        print("start_learning")
        lc = self.connected_robots[arm]["learning_config"]
        status = self.connected_robots[arm]["mios_status"]
        mls_status = self.connected_robots[arm]["mls_status"]
        obj = self.connected_robots[arm]["grasped_object"]
        if not lc:
            logger.error("no learning configuration added")
            return False
        print("start_learning2")
        insertable = lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]
        self.update_state()
        #if self.connectivity != "connected":  # it should be connected by now...
        #    logger.error("Cannot start learning, because connectivity != connected ("+str(self.connectivity)+")")
        #    return False
        print("start_learning3")
        if status != "Idle":
            logger.error("Cannot start learning, because mios_status != connected ("+str(self.connectivity)+")")
            return False
        print("start_learning4")
        if mls_status != "running":
            logger.error("ml_service is not running or busy")
            return False
        if obj != insertable:
            self.raise_hand(arm)
            return False
        print("start_learning5")
        #if not self.move_to_approach_pose(insertable):
        #    logger.error("Cant move to approach pose")
        #    return False
        
        self.connected_robots[arm]["alert"] = False
        s = ServerProxy("http://" + self.ip + ":"+str(self.connected_robots[arm]["mls_port"]), allow_none=True)
        lc_dict = lc.to_dict()
        print("start_learning6: agents:",lc.pd.host," tags:",lc.pd.tags, "\npd:: ",lc_dict["pd"])

        if self.connected_robots[arm]["current_problem_uuid"] is not None:  
            logger.debug(f"Learning {insertable} already started")
            time.sleep(1)
            if self.connected_robots[arm]["learning_started"]:
                return self.connected_robots[arm]["current_problem_uuid"]  # already started by other collective_manager
            
        self.connected_robots[arm]["current_problem_uuid"] = s.start_service(lc_dict["pd"], lc_dict["sc"], [lc.pd.host], lc_dict["knowledge"],
                                                    {"exp_name":lc.pd.tags[0], "iteration":lc.pd.tags[1]})
        print("start_learning7")
        logger.info("started learning "+str(insertable)+":"+str(self.connected_robots[arm]["current_problem_uuid"]))
        self.connected_robots[arm]["learning_started"] = True
        self.connected_robots[arm]["current_experiment"] = "/".join(lc.pd.tags[:3]) + "/"
        return self.connected_robots[arm]["current_problem_uuid"]

    def check_pose(self, pose, arm="left"):
        if arm == "left":
            response = call_method(self.ip, self.connected_robots[arm]["mios_port"], "download_object_context", {"object": pose})
        if arm == "right":
            response = call_method(self.ip, self.connected_robots[arm]["mios_port"], "download_object_context", {"object": pose})
        if type(response) is not dict:
            self.update_state()
            return False
        if "error" in response["result"]:
            return False
        return response["result"]["context"]
    
    def finished(self, uuid, arm):
        if self.connected_robots[arm]["learning_started"]:
            return False
        ml_results = self.connected_robots[arm]["mongo"].read("ml_results","insertion",{"meta.uuid":uuid})
        if len(ml_results)!=1:
            return False
        if "final_results" not in ml_results[0]:
            return False
        return True

    
class CollectiveExperiment:
    def __init__(self, name:str, modules:dict, problem_definitions:list[dict] = None, knowledge_configs:list[dict] = None,
                  service_configs:list[dict] = None, arms:list[str] = [], n_agents:int = False, keep_allocation:bool = False, global_db_ip:str = "10.157.175.119"):
        '''
        modules: dict of CollectiveModules used in this experiment; {"<hostname>": {"rpc-proxy":CollectiveModule(), "lock":threading.Lock()}...}
        '''
        self.name = name
        self.modules = modules
        self.global_db_ip = global_db_ip
        self.problem_definitions = problem_definitions
        self.knowledge_configs = knowledge_configs
        self.service_configs = service_configs
        self.n_agents = n_agents  # number of concurrently learning agents
        self.keep_allocation = keep_allocation
        self.keep_running = False
        self.finished = False
        self.task_allocation_thread = None
        self.ready = False
        self.learning_queue = PriorityQueue()
        self.learning_threads = []
        self.arms = arms
        self.active_modules = set()

        self.exp_state = dict()

        for i,_ in enumerate(problem_definitions):
            self.exp_state["s"+str(i)] = {}
            self.exp_state["s"+str(i)]["module"] = problem_definitions[i]["host"]
            self.exp_state["s"+str(i)]["arm"] = arms[i]
            self.exp_state["s"+str(i)]["skill_class"] = problem_definitions[i]["skill_class"]
            self.exp_state["s"+str(i)]["skill_instance"] = problem_definitions[i]["skill_instance"]
            self.exp_state["s"+str(i)]["state"] = "no Information"  # queued, started, learned, 
            self.exp_state["s"+str(i)]["t_start"] = False
            self.exp_state["s"+str(i)]["t_end"] = False
            self.exp_state["s"+str(i)]["external_knowledge"] = []  # knowledge found in the beginning of the task (slow pipe)
            self.exp_state["s"+str(i)]["mls_uuid"] = False
            self.exp_state["s"+str(i)]["lock"] = threading.Lock()

        
        logger.debug("exp_state dict: \n"+ pprint.pformat(self.exp_state,indent=4))    
        
        # self.tasks = dict()
        # for i,pd in enumerate(self.problem_definitions):
        #     #check if module is available
        #     if pd.host not in self.modules.keys():
        #         logger.error("Problem Definition referese to host that is not part of the experiment: " + pd.host)
        #         continue
        #     #create task dictionary
        #     if pd.host not in self.tasks:
        #         self.tasks[pd.host] = []
        #     self.tasks[pd.host].append({"insertable":pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"],
        #                                 "index":i,
        #                                 "mls_uuid": None})
            
    def get_modules(self):
        return self.modules


    def precheck(self):
        for arm, pd in zip(self.arms, self.problem_definitions):
            if pd["host"] not in self.modules.keys():
                logger.error("Problem Definition referese to host that is not part of the experiment: " + pd["host"])
                return False
            self.modules[module][arm]["lock"].acquire()
            module = self.modules[pd["host"]][arm]["rpc-proxy"]
            #module.update_state()
            insertable = pd["default_context"]["skills"]["insertion"]["skill"]["objects"]["Insertable"]
            print("precheck: ", arm)
            if not module.check_pose(insertable, arm):
                self.modules[module][arm]["lock"].release()
                return False
            if not module.check_pose(pd["default_context"]["skills"]["insertion"]["skill"]["objects"]["Container"],arm):
                self.modules[module][arm]["lock"].release()
                return False
            if not module.check_pose(pd["default_context"]["skills"]["insertion"]["skill"]["objects"]["Approach"],arm):
                self.modules[module][arm]["lock"].release()
                return False
            if not module.check_pose(pd["default_context"]["skills"]["insertion"]["skill"]["objects"]["Container"]+"_above",arm):
                self.modules[module][arm]["lock"].release()
                return False
            # if not module.check_pose(insertable+"_box", arm):
            #     return False
            # if not module.check_pose(insertable+"_box_container", arm):
            #     return False
            # if not module.check_pose(insertable+"_box_container_approach", arm):
            #     return False
            # if not module.check_pose(insertable+"_box_container_above", arm):
            #     return False
            # if not module.check_pose("default", arm):
            #     return False
            # if not module.check_pose(insertable+"_camera_left", arm):
            #     return False
            # if not module.check_pose(insertable+"_camera_right", arm):
            #     return False
            # if not module.check_pose(insertable+"_camera_left_above", arm):
            #     return False
            # if not module.check_pose(insertable+"_camera_right_above", arm):
            #    return False
            if not module.check_pose("raise_hand",arm):
                self.modules[module][arm]["lock"].release()
                return False
            #check if tags are already available at Module
            if not module.check_tags_unused(pd["tags"]):
                self.modules[module][arm]["lock"].release()
                logger.warning("Tags are alreay in use: "+str(pd["tags"]))
                return False
            self.modules[module][arm]["lock"].release()
        return True
            
    def _task_allocation_strict(self):  #currently not working. ready to learn is only True when camera is in place. Camera is only moving in place when there is a next task in learning sequence
        '''
        this implements a task allocation that strictly allocated according to the input sequence (FIFO)
        '''
        all_queued = False
        index = 0
        while self.keep_running:
            n_tasks = len(self.exp_state) - 1  # "state" key in self.exp_state is not an actual task
            for i in range(n_tasks):
                if self.exp_state["s"+str(i)]["state"] == "not started":  # found next task that is not started
                    module = self.exp_state["s"+str(i)]["module"]
                    insertable = self.exp_state["s"+str(i)]["skill_instance"]
                    lc = LearningConfig(pd=self.problem_definitions[i],
                                            sc=self.service_configs[i],
                                            knowledge=self.knowledge_configs[i],arm=self.arms[i])
                    arm = self.arms[i]
                    self.modules[module][arm]["lock"].acquire()
                    if self.modules[module][arm]["rpc-proxy"].ready_to_learn(insertable):  # if object are grasped
                        if self.modules[module][arm]["rpc-proxy"].get_state()["arm"]["learning_config"] is None:
                            self.modules[module][arm]["rpc-proxy"].add_learning_config(pd=lc.pd.to_dict(), sc=lc.sc.to_dict(), knowledge=lc.knowledge.to_dict(),priority=0,arm=arm,experiment_name=self.name)
                        self.learning_queue.put((index, lc))
                        self.exp_state["s"+str(i)]["state"] = "queued"
                        index += 1
                        self.modules[module][arm]["lock"].release()
                        break
                    elif self.modules[module][arm]["rpc-proxy"].get_state()["arm"]["learning_config"] is None:  #set next lc (so module raises arm)
                        self.modules[module][arm]["rpc-proxy"].add_learning_config(pd=lc.pd.to_dict(), sc=lc.sc.to_dict(), knowledge=lc.knowledge.to_dict(),priority=0,arm=arm,experiment_name=self.name)
                    elif self.name not in self.modules[module][arm]["rpc-proxy"].get_state()["arm"]["learning_config"]["pd"]["tags"]:
                        logger.error("different experiment is blocking next task: " + str(lc.pd.tags))
                        self.modules[module][arm]["lock"].release()
                        time.sleep(3)
                        break
                    self.modules[module][arm]["lock"].release()
                    break
                all_queued = True
            if all_queued:
                break
        return True
    
    def _task_allocation_module(self):
        n_tasks = len(self.problem_definitions)
        for i in range(n_tasks):
            logger.debug(self.name+": add learning configuration for "+self.problem_definitions[i].skill_instance +" to "+self.exp_state["s"+str(i)]["module"]+".")
            module = self.exp_state["s"+str(i)]["module"]
            arm = self.exp_state["s"+str(i)]["arm"]
            self.modules[module][arm]["lock"].acquire()
            self.modules[module][arm]["rpc-proxy"].add_learning_config(pd=self.problem_definitions[i].to_dict(),sc=self.service_configs[i].to_dict(),knowledge=self.knowledge_configs[i].to_dict(),
                                                              priority=n_tasks-i,arm=self.exp_state["s"+str(i)]["arm"],experiment_name=self.name)
            self.modules[module][arm]["lock"].release()
            self.exp_state["s"+str(i)]["state"] = "queued"
            #self.learning_queue.put((i, LearningConfig(pd=self.problem_definitions[i], sc=self.service_configs[i], knowledge=self.knowledge_configs[i],arm=self.exp_state["s"+str(i)]["arm"])), block=False)
        return True

    
    def _learner_thread(self):
        print("start learning thread")
        while self.keep_running:
            still_learning=False
            
            for key, state in self.exp_state.items():
                if key == "meta":
                    continue
                #logger.info("state\n"+str(state))
                module = state["module"]  #hostname
                arm = state["arm"]
                if not self.modules[module][arm]["lock"].acquire(False):
                    continue
                
                if state["state"] != "queued":
                    self.modules[module][arm]["lock"].release()
                    continue
                still_learning=True  # just to indicate if there are sill tasks to learn
                
                
                insertable = state["skill_instance"]
                try:
                    if not self.modules[module][arm]["rpc-proxy"].preconditions_fullfilled(arm, insertable):  
                        self.modules[module][arm]["lock"].release()
                        continue
                except ConnectionRefusedError:
                    #logger.error("ConnectionRefusedError for host "+module)
                    self.modules[module][arm]["lock"].release()
                    continue

                print("start learning ",insertable)
                mls_uuid = self.modules[module][arm]["rpc-proxy"].start_learning(arm)
                
                if not mls_uuid:
                    logger.error("no learning uuid for "+insertable+"  received from "+module)
                    self.modules[module][arm]["lock"].release()
                    continue
                state["t_start"] = time.time()
                state["mls_uuid"] = mls_uuid
                state["state"] = "started"

                time.sleep(5)
                connection_refused_count = 0
                while True:
                    if connection_refused_count>=10:
                        break
                    try:
                        if not self.modules[module][arm]["rpc-proxy"].finished(mls_uuid, arm):
                            connection_refused_count=0
                            time.sleep(5)
                            state["t_end"] = time.time()
                        else:
                            break
                    except ConnectionRefusedError:
                        connection_refused_count += 1
                        logger.error("_leaner_thread: Connection to ml_service refussed. Trying again..."+str(connection_refused_count))
                        time.sleep(5)
                    except Fault:
                        connection_refused_count += 1
                        logger.error("_leaner_thread: ml service not running. Trying again..."+str(connection_refused_count))
                        time.sleep(5)
                print("learning ",insertable, "finished")
                state["state"] = "learned"
                self.modules[module][arm]["lock"].release()
            if not still_learning:
                print("no more task to learn. Stopping learner thread")
                break
        print("learning thread finished")
        logger.debug("Learning Thread finished") 

    def run_experiment(self):
        logger.debug("Experiment "+self.name + ": run_experiment")
        self.keep_running = True
        
        #assume prechecks are done
        #put tasks into learning queue:
        if not self.keep_allocation:
            logger.debug("Experiment "+self.name + ": only module vise allocaiton sequence. No global allocation sequence")
            # throw all tasks in learning-queue at once, if worker thread takes task which is not able to start it will be put back 
            # (this can change the allocation sequence)
            # baiscally it is a greedy allocation strategy that learnes a task as soon as it is available.
            index = 0
            priority = len(self.problem_definitions)
            # deploy all pd to modules:

            for i, (pd,sc,knowledge,arm) in enumerate(zip(self.problem_definitions, self.service_configs, self.knowledge_configs,self.arms)):
                #lc = LearningConfig(pd=pd, sc=sc, knowledge=knowledge,arm=arm,priority=priority)
                #self.learning_queue.put((index, LearningConfig(pd=pd, sc=sc, knowledge=knowledge,arm=arm)), block=False)
                index += 1
                module = pd["host"]
                self.modules[module][arm]["lock"].acquire()
                module_state = self.modules[module][arm]["rpc-proxy"].get_state()
                self.modules[module][arm]["lock"].release()
                if module_state is None:
                    print("module_state is None")
                    continue
                if type(module_state) is not dict:
                    logger.debug("Module state is not dict. Investigate this! "+module+" "+arm)
                    print("Module state is not dict. Investigate this! "+module+" "+arm)
                    continue
                if arm not in module_state:
                    logger.error(module+" has no"+arm+" arm. Skipping...")
                    print(module+" has no"+arm+" arm. Skipping...")
                    continue
                # set learning config:
                self.modules[module][arm]["lock"].acquire()
                self.modules[module][arm]["rpc-proxy"].add_learning_config(pd, sc, knowledge,priority,arm,self.name)
                self.modules[module][arm]["lock"].release()
                print("added learning object",pd["skill_instance"]," module to ",str(module))
                print("knowledge: ",knowledge["meta"]["mode"])
                self.exp_state["s"+str(i)]["state"] = "queued"
                priority -= 1

        else:
            # create thread that shovels next tasks (according to allocation sequence) into learning-queue only if they can be started imediatly
            logger.debug("Experiment "+self.name + ": start allocation thread")
            self._task_allocation_module()
            #self.task_allocation_thread = Thread(target=self._task_allocation_module)
            #self.task_allocation_thread.start()
            
        for host, module in self.modules.items():
            logger.debug("Experiment "+self.name + ": start module on "+host)
            time.sleep(0.5)
            for arm in module.keys():
                module[arm]["lock"].acquire()
                module[arm]["rpc-proxy"].start_monitoring(self.global_db_ip, self.name)
                module[arm]["lock"].release()
        
        for i in range(self.n_agents):
            self.learning_threads.append(Thread(target=self._learner_thread, name="leaner"+str(i)))
            self.learning_threads[-1].start()

        # problem queue fifo and solved list
        # go through problem queue and assign next possible or next task to worker thread -> running heap
        # worker threads n_agents
        
        # START MODULE SUPERVISIONS threads

        #self.learning_queue.join()
        for t in self.learning_threads:
            t.join()
        logger.info("learning threads are finished.")
        self.stop_experiment()

    def stop_experiment(self):
        self.keep_running = False
        for host, m in self.modules.items():
            logger.debug("Experiment "+self.name + ": start module on "+host)
            arms = ["left"]
            with ServerProxy(f"http://{host}:8010") as p:
                arms = p.get_arms()
            for arm in arms:
                m[arm]["rpc-proxy"].stop_monitoring()
                m[arm]["rpc-proxy"].reset()
        reseted = False
        while not reseted:  #wait until all are reseted...
            reseted = True
            for m in self.modules.values():
                if not m[arm]["rpc-proxy"].is_reseted(arm):
                    reseted=False
            time.sleep(1)

    def append_task(self, module, pd, knowledge_config, sc):
        # append also self.exp_state
        pass
        
class CollectiveManagerServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

class CollectiveManager:
    def __init__(self, modules:list = None, database="10.157.175.119"):
        '''
        Point of interaction with the collective (PD.RAI)
        Inputs: modules: list - list of hostnames of the modules that will be managed with this class
                database: str - hostname or ip of MongoDB
        '''
        self.rpc_port = 8006
        self.module_names = set()
        self.modules = dict()
        if type(modules) is list:
            self.module_names = set(modules)
            self._update_modules()
        self.database_ip = database
        self.database_client = MongoDBClient(database)
        
        self.experiments = dict()
        self.running_experiments = set()
        self.experiment_threads = dict()
        self.rpc_server = CollectiveManagerServer(("0.0.0.0", self.rpc_port), allow_none=True)
    
    def start_rpc_server(self):
        logger.debug("CollectiveManager started on port "+str(self.rpc_port))
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.add_experiment, "add_experiment")
        self.rpc_server.register_function(self.start_experiment, "start_experiment")
        self.rpc_server.register_function(self.add_module, "add_module")
        self.rpc_server.register_function(self.remove_module, "remove_module")
        self.rpc_server.register_function(self.get_experiments, "get_experiments")
        self.rpc_server.register_function(self.get_modules, "get_modules")
        self.rpc_server.register_function(self.describe_experiment, "describe_experiment")
        self.rpc_server.register_function(self.remove_experiment, "remove_experiment")
        self.rpc_server.serve_forever()
        logger.debug("CollectiveManager stopped")
    
    def add_module(self, module):
        '''
        Adds an module (hostname) to the managed collective
        '''
        if type(module) is list:
            for a in module:
                self.module_names.add(a)
        elif type(module) is str:
            self.module_names.add(module)
        else:
            logger.error("Invalid input type. Accepted input is list or str.")
            return False
        return self._update_modules()

    def remove_module(self, module):
        if type(module) is list:
            for a in module:
                self.module_names.remove(a)
        elif type(module) is str:
            self.module_names.remove(module)
        else:
            logger.error("Invalid input type. Accepted input is list or str.")
            return False
        return self._update_modules()

    def _update_modules(self):
        #remove deleted ones:
        remove_these = []
        for a in self.modules.keys():
            if a not in self.module_names:
                remove_these.append(a)
        for a in remove_these:
            #self.modules[a][arm]["rpc-proxy"].delete()
            self.modules.pop(a)
        #add new ones:
        for a in self.module_names:
            if a not in self.modules:
                arms = ["left"]
                with ServerProxy("http://"+a+":8010",allow_none=True) as proxy:
                    try:
                        arms = proxy.get_arms()
                    except Exception as e:
                        print(f"An error occurred when calling module {a} -> {e}")
                logger.debug(f"Module {a}: connected arms: {str(arms)}")
                self.modules[a] = {}
                for arm in arms:
                    self.modules[a][arm] = {
                                        "rpc-proxy":ServerProxy("http://"+a+":8010",allow_none=True),  # RPC Client for real deployment    # CollectiveModule(a)  # for non RPC testing phase
                                        "lock":threading.Lock()
                                        }
        logger.debug("managing "+str(len(self.modules))+" modules")
        print("updating modules to : \n",self.modules)
        return len(self.modules) == len(self.module_names)

    def add_experiment(self, name:str, modules:list, problem_definitions:list, knowledge_configs:list, service_configs:list, arms:list,
                       n_agents:int = False, keep_allocation:bool = False, iteration:int = 0):
        '''
        Adds experiment definitions to be executed on the collective. All input lists have to have the same order
        input:  name: str
                This is the name of this single experiment, eg. "charlie_1"
        
                modules: list
                This list has the same length as the problem_definitons list. It contains all hostnames for the single learning problems. 
        
                problem_definitons: list
                The list can contain problem_definitions dicts directly (like the ones created with InsertionFactory get_proble_definition())
                Or it can contain all insertables. With this option, the problem_definions are created automatically for insertion 
                with default values and a norm for naming poses.

                knowledge_configs: list
                This is a list of dicts containing the knowledge configurations for the every problem_definiton that is learned.
                If there is only one dict inside the list, it is used for every problem_definition.

                service_configs: list
                This is a list of dicts containing the service configurations for the every problem_definiton that is learned.
                If there is only one dict inside the list, it is used for every problem_definition.

                n_agents: int
                This sets the number of concurrent learning modules

                keep_allocation: bool
                If True, the sequence of problems is keept during the experiment
                If False, this sequence is allowed to change to increase learning throughput
        '''
        #check type:
        logger.debug("add_experiment with name "+name)
        if type(problem_definitions) != list or type(knowledge_configs) != list or type(service_configs) != list:
            logger.error("Type of input is not matching type(list)")
            return False
        #check length:
        #if len(modules) != len(problem_definitions):
        #    logger.error("Length of modules and problem_definitions doesn\'t match.")
        #    return False
        if len(problem_definitions) != len(service_configs):
            if len(service_configs) == 1:
                service_configs = service_configs*len(problem_definitions) #same service config for all problems
            else:
                logger.error("Number of service_configs (" + str(len(service_configs)) + 
                             ") does\'t match number of problem_definitions (" + str(len(problem_definitions)))
                return False  
        if len(problem_definitions) != len(knowledge_configs) :
            if len(knowledge_configs) == 1:
                knowledge_configs = knowledge_configs*len(problem_definitions) #same service config for all problems
            else:
                logger.error("Number of knowledge_configs (" + str(len(knowledge_configs)) + 
                             ") does\'t match number of problem_definitions (" + str(len(problem_definitions)))
                return False
        if len(problem_definitions) != len(arms):
            if len(arms) == 1:
                arms = arms*len(problem_definitions) #same service config for all problems
            else:
                logger.error("Number of arms (" + str(len(service_configs)) + 
                             ") does\'t match number of problem_definitions (" + str(len(problem_definitions)))
                return False  
        #check if modules are managed by collective manager
        for module in modules:
            if module not in self.module_names:
                return False
            
        for i,pd in enumerate(problem_definitions):
            
            #check type
            if type(pd) is tuple:
                #create full problem_definitions
                insertable = copy.deepcopy(pd[1])
                host = copy.deepcopy(pd[0])
                problem_definitions[i] = InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": insertable+"_container",
                                    "Approach": insertable+"_container_approach"}).get_problem_definition(insertable)
                problem_definitions[i].host = host
            elif type(pd) is dict:
                print("creating ProblemDefinition object from dicts")
                problem_definitions[i] = ProblemDefinition.from_dict(pd)
            else:
                logger.error("Falty problem_definition type discovered: " + str(type(pd)))
                return False
            if not problem_definitions[i].host:
                print("modify pd.host to ",modules[i])
                problem_definitions[i].host = modules[i]
            print("add problem_definition",problem_definitions[i].tags," to ",problem_definitions[i].host)
            problem_definitions[i].tags.insert(0,name)
            if iteration:
                problem_definitions[i].tags.insert(1,"iteration_"+str(iteration))
            problem_definitions[i].tags.insert(2,str(problem_definitions[i].skill_instance))
            problem_definitions[i].tags.insert(3,str(problem_definitions[i].host))
            problem_definitions[i] = problem_definitions[i].to_dict()


        logger.debug("add experiment "+name)
        self.experiments[name] = CollectiveExperiment(name = name,
                                                        modules=self.modules, #{hostname: module for hostname, module in self.modules.items() if hostname in modules},
                                                        problem_definitions=problem_definitions,
                                                        knowledge_configs=knowledge_configs,
                                                        service_configs=service_configs,
                                                        arms=arms,
                                                        n_agents=n_agents,
                                                        keep_allocation=keep_allocation,
                                                        global_db_ip=self.database_ip)
    
    def remove_experiment(self, name:str):
        if name not in self.experiments:
            return False
        if self.experiments[name].keep_running:
            self.experiments[name].stop_experiment()
            self.experiment_threads[name].join()
            self.running_experiments.remove(name)
        
        self.experiments.pop(name)
        return True

    def start_experiment(self, name:str):

        if name not in self.experiments:
            logger.error("No experiment available with name "+name)
            return False
        self.running_experiments.add(name)
        if name in self.experiment_threads:
            logger.error("Experiment with name "+str(name)+" is already running")
            return False
        #precheck = self.experiments[name].precheck()
        #if not precheck:
        #    return {"precheck": precheck}
        self.experiment_threads[name] = Thread(target=self.experiments[name].run_experiment)
        self.experiment_threads[name].start()
        return True
    
    def get_experiments(self):
        return list(self.experiments.keys())

    def get_modules(self):
        return list(self.modules)
    
    def describe_experiment(self, name):
        running = True if name in self.running_experiments else False
        return {"running": running, "experiment_state": self.experiments[name].exp_state}
    

class CollectiveClient:
    def __init__(self):
        self.collective_manager_ip = None

