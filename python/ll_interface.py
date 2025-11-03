import struct
import socket
import time
from utils.ws_client import *

PI = 3.141592653
INIT_q = [0, -3.141592653/4, 0, -3 * PI/4, 0, PI/2, PI/4]

class InterfaceNotFound(Exception):
    print("Interface need to be defined with  \"JointPose\", \"CartPose\", \"Twist\", \"Wrench\" or \"Torque\"")
    pass
class LLSender:
    def __init__(self, ip,  sender_ip, interface, init_q: list = []) -> None:
        """
        ip - network address of the mios instance controlling the robot
        sender_ip - network address of the of this PC (same network than <ip>)
        interface - low level interface type, eg. "JointPose", "CartPose", "Twist", "Wrench", "Torque"
        init_q - initial joint angles
        """
        self.robot_ip = ip
        self.own_ip = sender_ip
        self.mode = None
        self.robot_llport = 8889
        self.own_port = 8888
        self.init_q = init_q
        if interface == "JointPose" or interface == "CartPose" or interface == "Twist" or interface == "Wrench" or interface == "Torque" :
            self.mode = interface
        else:
            raise InterfaceNotFound

    def _udp_send_message(self, ip, port, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(message).encode(), (ip, port))

    def _udp_receive_message(self, ip, port): 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
        s.bind((ip, port)) 
        try: 
            data, adrr = s.recvfrom(8192)
            s.close()
        except KeyboardInterrupt:
            s.close()
            return False, (False, False)
        return json.loads(data.decode("utf-8")), adrr
    
    def _udp_send_message_teleformat(self, ip, port, payload:list, counter=0):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(type(payload))
        format = "<6b"+str(len(payload))+"f4b"  # 127,127,127,127,package counter, payload size, payload (4 bytes/value), 126,126,126,126
        message = struct.pack(format, 127,127,127,127, counter, len(payload)*4,*payload, 126,126,126,126)
        sock.sendto(message, (ip, port))

    def start(self):
        if self.mode == "JointPose":
            controller = 1
        elif self.mode == "Torque":
            controller = 1
        elif self.mode == "CartPose":
            controller = 0
        elif self.mode == "Wrench":
            controller = 0 
        elif self.mode == "Twist":
            controller = 0
        else:
            raise InterfaceNotFound

        llInterface_context = {
            "skill": {
                "ip_dst": self.own_ip,  # IP to send answers to
                "port_dst": self.own_port,  # port to send answers to
                "port_src": self.robot_llport,  # receiving port
                "LLInterface_mode": self.mode,
                "twist": {"static_frame": True}  # if self.mode is Twist
            },
            "control": {
                "control_mode": controller,
                "joint_imp": {
                   "K_theta": [2500,2200,2800,2600,2300,2200,250]
                },
                "cart_imp": {
                   "K_x": [10, 10, 10, 2.5, 2.5, 2.5]
                }
            }
        }    
        t = Task(self.robot_ip)
        t.add_skill("remote_"+self.mode, "LLInterface", llInterface_context)
        t.start()
        if not self.init_q:
            self.init_q = INIT_q  # for quick testing
        call_method(self.robot_ip,12000,"post_event",{"name":"handshake","content":{"q_init":self.init_q}})
        print(self.own_ip)
        result, addr = self._udp_receive_message(self.own_ip, 8888)
        self._udp_send_message(addr[0], addr[1], {"result":True}) 
        print(result)
    
    def stop(self):
        call_method(self.robot_ip, 12000, "stop_task")

    def send(self, payload):
        self._udp_send_message_teleformat(self.robot_ip, self.robot_llport, payload)


class Task:
    def __init__(self, robot, port=12000):
        self.skill_names = []
        self.skill_types = []
        self.skill_context = dict()
        self.context = {
            "parameters": {
                "skill_names": [],
                "skill_types": [],
                "as_queue": False
            },
            "skills": self.skill_context
        }

        self.robot = robot
        self.port = port
        self.task_uuid = "INVALID"
        self.t_0 = 0

    def add_skill(self, name, skill_class, context):
        self.skill_names.append(name)
        self.skill_types.append(skill_class)
        self.skill_context[name] = context

        self.context["parameters"]["skill_names"] = self.skill_names
        self.context["parameters"]["skill_types"] = self.skill_types
        self.context["skills"] = self.skill_context

    def start(self, queue: bool = False):
        self.t_0 = time.time()
        self.context["parameters"]["as_queue"] = queue
        response = start_task(self.robot, "GenericTask", parameters=self.context, port=self.port)
        self.task_uuid = response["result"]["task_uuid"]

    def wait(self):
        result = wait_for_task(self.robot, self.task_uuid, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result

    def stop(self):
        result = stop_task(self.robot, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result





#  useful functions:
def subscribe_telemetry(robot_ip, receiving_ip, receiving_port, data:list, loop=False):
    '''
    let mios send current state
    robot_ip - where mios is running
    reveiving_ip, receiving_port - where do you want to receive the data
    data - list of strings; what kind of data do you whish. Possible strings:
        //End effector pose in origin frame (O).
                        "O_T_EE",
                    //End effector pose in task frame (TF).
                        "T_T_EE",
                    //Link-side joint pose.
                        "q"
                    //Link-side joint velocities.
                        "dq"
                    //Motor-side joint pose.
                        "theta"
                    //Motor-side joint velocities.
                        "dtheta"
                    //Cartesian twist in origin frame (O).
                        "O_dX_EE"
                    //Cartesian twist in end effector frame (EE).
                        "EE_dX_EE"
                    //Cartesian twist in task frame (TF).
                        "TF_dX_EE"
                    //Estimated external torques.
                        "tau_ext"
                    //Joint torques.
                        "tau_j"
                    //Estimated external wrench at TCP in stiffness frame (K).
                        "K_F_ext_K"
                    //Derivative of estimated external wrench at TCP in stiffness frame (K).
                        "K_dF_ext_K"
                    //Estimated external wrench at TCP in origin frame (O).
                        "O_F_ext_K"
                    //Derivative of estimated external wrench at TCP in origin frame (O).
                        "O_dF_ext_K"
                    //Estimated external wrench at TCP in task frame (TF).
                        "TF_F_ext_K"
                    //Derivative of estimated external wrench at TCP in task frame (TF).
                        "TF_dF_ext_K"
                        "finger_width"
                        "finger_temperature"
                        "is_grasping"
                    //Mass matrix.
                        "M"
                    //Coriolis vector.
                        "C"
                    //Gravity vector.
                        "G"
                    //Body jacobian.
                        "B_J_EE"
                    //Zero jacobian. 
                        "B_J_O"
                        "max_finger_width"
                        "hand_activity_state"
                    //Rho factor from force controllers's shaping function.
                        "e"
                        "rho"
                        "K_x"
                        "xi_x"
                        "K_theta"
                        "xi_theta"
                        "TF_T_EE_d"
                        "TF_dX_d"
                        "TF_F_ff"
                        "O_R_T"
                        "q_d"
                        "dq_d"
                        "tau_ff"

    '''
    call_method(robot_ip,12000, "subscribe_telemetry",{"subscribe":data,"ip":receiving_ip,"port":receiving_port})
    if loop:
        robot_state = write_incomming_udp(receiving_ip, receiving_port)
    else:
        robot_state = udp_receiver(receiving_ip,receiving_port)
    call_method(robot_ip,12000, "unsubscribe_telemetry",{"subscribe":data,"ip":receiving_ip,"port":receiving_port})

    return robot_state

def udp_receiver(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    s.bind((ip, port)) 
    data_dict = None
    try:
        data, adrr = s.recvfrom(8192) 
        data_dict = json.loads(data.decode("utf-8"))
        s.close()
    except KeyboardInterrupt:
        pass
    return data_dict

def write_incomming_udp(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    s.bind((ip, port)) 
    try:
        print("listening at ", ip, ":", port,"\n")
        print("   --- Interrupt writing ctrl+c ---")
        while True: 
            data, adrr = s.recvfrom(8192) 
            data_dict = json.loads(data.decode("utf-8"))
            for key, value in data_dict.items():
                if type(value) == list:
                    print(key, ": ", [float("{0:0.2f}".format(v)) for v in value])
                else: 
                    print(key, ": ", value)
    except KeyboardInterrupt:
        s.close()
    return True





################# recovery related
def move_joint(robot, location,port=12000, wait=True):
   
    move_context = {
        "skill": {
            "speed": 0.5,
            "acc": 1,
            "q_g": [0, 0, 0, 0, 0, 0, 0],
            "objects": {
                "goal_pose": "GoalPose"
            }
        },
        "control": {
            "control_mode": 3
        },
        "user": {
            "env_X": [0.005, 0.005, 0.005, 0.0175, 0.0175, 0.0175]
        }
    }
    move_context["skill"]["objects"]["goal_pose"] = location
    move_context["skill"]["time_max"] = 10
    t0 = Task(robot, port=port)
    t0.add_skill("move", "MoveToPoseJoint", move_context)
    t0.start()
    if wait:
        return t0.wait()
    
def extract(ip, obj_nr):
    extraction_context = {
        "skill": {
            "objects": {
                "Container": "hold",
                "ExtractTo": obj_nr + "_left_container_approach",
                "Extractable": obj_nr + "_left"
            },
            "time_max": 15,
            "p0": {
                "search_a": [0, 0, 0, 0, 0, 0],
                "search_f": [0, 0, 0, 0, 0, 0],
                "K_x": [1500, 1500, 1500, 150, 150, 150],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p1": {
                "dX_d": [0.05, 0.25],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1500, 100, 100, 100]
            }
        },

        "control": {
            "control_mode": 0  # 0" non-feedback;  1" feedback-xy; 2" ...
        },
        "user": {
            "env_X": [0.005, 0.01, 0.01, 0.05, 0.05, 0.05],
            "env_dX": [0.001, 0.001, 0.001, 0.005, 0.005, 0.005]
        }
    }
    
    t = Task(ip)
    t.add_skill("extraction", "TaxExtraction", extraction_context)
    t.start()
    time.sleep(0.1)
    result = t.wait()


def extract_and_reset(ip, obj_nr):
    extract(ip, obj_nr)
    # move arms to pre-start pose
    move_joint(ip, obj_nr + "_left_container_approach", 12000)
    move_joint(ip, "hold", 13000)
