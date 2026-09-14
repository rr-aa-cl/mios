import os
import math
from utils.ws_client import *
import json
import socket
import time


TEACHING_GRASP_SPEED = 1.0  # m/s, requested speed for grasp and move commands
TEACHING_GRASP_FORCE = 100.0  # N; also saved for subsequent object grasps
TEACHING_REGRASP_CLEARANCE = 0.005  # m, opening added before grasp_object
_MAX_GRASP_WIDTH = 0.08  # m
_GRASP_WIDTH_STABILITY = 0.0002  # m
# Core accepts gripper feedback up to 500 ms old. Spacing reads farther apart
# avoids treating the same cached sample as confirmation that motion settled.
_GRASP_FEEDBACK_INTERVAL = 0.55  # s


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
        self._start_attempted = False
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
        self.task_uuid = "INVALID"
        self._start_attempted = True
        response = start_task(self.robot, "GenericTask", parameters=self.context, port=self.port)
        if (isinstance(response, dict) and isinstance(response.get("result"), dict)
                and response["result"].get("result") is False):
            self._start_attempted = False
        _portal_result_or_raise(response, "Start task")
        task_uuid = response["result"].get("task_uuid")
        if not isinstance(task_uuid, str) or not task_uuid or task_uuid == "INVALID":
            raise RuntimeError("Start task failed: Portal did not return a valid task UUID.")
        self.task_uuid = task_uuid

    def wait(self):
        result = wait_for_task(self.robot, self.task_uuid, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result

    def stop(self):
        result = stop_task(self.robot, empty_queue=True, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result

def get_ip(hostname: str):
    print("hostname: ",hostname)
    return socket.gethostbyname(hostname)

def populate_database(host:str, db:str, ip:str, user_name="franka", user_pw="frankaRSI"):
    '''
    host: mios IP
    db: mios Database (typically miosL)
    ip: IP of Robot ControlBox connected to the mios PC
    user_name: DESK username
    user_pw: DESK user password
    '''
    try:
        # Most examples use only the Portal client.  Keep MongoDB optional so
        # teaching and dry-run entry points work without pymongo installed.
        from desk.mongodb_client import MongoDBClient
        client = MongoDBClient(host)
        new_params = {"desk_name":user_name, "desk_pwd":user_pw,"robot_ip":ip, "spoc_token":"","spoc_in_control":False}
        client.update(db,"parameters",{"name":"system"}, new_params)
        print("updated ", host,": ",db)
    except:
            print(host, " not updated")

def teach_position(robot, position_name, teach_gripper_width=False):
    # Teaches the pose in Cartesian and joint space for the specified object. If the object does not existin a
    # new object is created. The object can also be a reference frame for other objects.
    # To teach panda have to be in guiding mode (white light at panda arm)
    return call_method(robot, 12000, "teach_object", {"object": position_name, "teach_width": teach_gripper_width})

def grasp(robot):
    # grasp sth smaller than 10cm (epsilon_outer=0.1)
    return call_method(robot, 12000, "grasp",
                       {"width": 0.0, "speed": 1, "force": 200, "epsilon_inner": 1, "epsilon_outer": 0.1})

def open_gripper(robot):
    # opens the gripper completely
    return call_method(robot, 12000, "release_object", {"speed": 1})

def move_gripper(robot,gripper_width):
    # open the gripper with gripper_width in [m] for e.g. 0.06 = 6cm
    return call_method(robot, 12000, "move_gripper", {"width": gripper_width, "speed": 0.15})

def set_grasped_object(robot, object_name):
    # set the grasped object so the robot know that it grabs something
    return call_method(robot, 12000, "set_grasped_object", {"object": object_name})


def move_to_contact(robot, location, port = 12000, wait=True):
    context = {
                "skill": {
                    "speed": 0.5,
                    "objects": {
                        "goal_pose": location
                    }
                },
                "control": {
                    "control_mode": 2
                },
                "user":{
                    "F_ext_contact": [10,5]
                }

            }
    t = Task(robot, port=port)
    t.add_skill("contact", "MoveToContact", context)
    t.start()
    if wait:
        return t.wait()

def move(robot:str, location:str, offset = [0,0,0], port=12000, wait = True,f_ext = [10,5], add_nullspace=False,
         p_g=[]):
    '''
    robot: ip of mios instance
    location: position name that was teached
    '''
    context = {
        "skill": {
            "p0":{
                "dX_d": [0.3, 0.8],
                "ddX_d": [0.5, 1],
                "K_x": [2000, 2000, 2000, 250, 250, 250],
                "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, offset[0], offset[1], offset[2], 1],
                "T_T_EE_g":p_g

            },
            "time_max":10,
            "objects": {
                    "GoalPose": location
                }
        },
        "control": {
            "control_mode": 0
        },
        "user":{
            "F_ext_max": f_ext,
            #"env_X": [0.002, 0.002, 0.002, 0.0175, 0.0175, 0.0175]  #[0.001, 0.001, 0.001, 0.001, 0.001, 0.001]
        }
    }
    if p_g:
        context["skill"]["objects"] = {}
    if add_nullspace:
        context["control"]["nullspace"] = {
                                                    "K_theta": [20, 20, 15, 10, 7, 5, 2],
                                                    "xi_theta": [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
                                                    "active": True
                                                    }
    t = Task(robot, port=port)
    t.add_skill("move", "TaxMove", context)
    t.start()
    if wait:
        return t.wait()

    #print("Result: " + str(result))

def init_position(robot):
    import math
    # move robot to start position
    M_PI_2 = math.pi / 2
    M_PI_4 = math.pi / 4
    initial_joint_pose = [0, -M_PI_4, 0, -3 * M_PI_4, 0, M_PI_2, M_PI_4]
    return start_task(robot, "MoveToJointPose", parameters={"parameters": {"q_g": initial_joint_pose, "pose":"NoneObject"}})


def move_joint(robot, location, port=12000, offset=[0,0,0,0,0,0,0], wait=True, speed = [], q_g=[]):
    '''
    robot: ip of mios instance
    location: position name that was teached
    '''
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    if not q_g:
        move_context["skill"]["objects"]["goal_pose"] = location
        move_context["skill"]["q_g_offset"] = offset
    else:
        move_context["skill"]["objects"]["goal_pose"] = "NoneObject"
        move_context["skill"]["q_g"] = q_g
    move_context["skill"]["time_max"] = 10
    move_context["user"]["env_X"] = [0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001]
    move_context["user"]["F_ext_max"] = [15,15]
    if speed:
        move_context["skill"]["speed"] = speed[0]
        move_context["skill"]["acc"] = speed[1]
    print(move_context)
    t0 = Task(robot, port=port)
    t0.add_skill("move", "MoveToPoseJoint", move_context)
    t0.start()
    if wait:
        return t0.wait()

def hold_pose(robot, duration, port, control="joint"):
    hold_context = {
        "skill": {
            "t_max": duration,
        },
        "control": {
            "control_mode": 1,
            "joint_imp":{
                "K_theta":[10000,10000,10000,10000,10000,10000,10000]
            }

        },
        #"user": {"F_ext_max": [100, 50]}
    }
    if control == "cart":
        hold_context["control"] = { "control_mode": 0,
                                    "cart_imp": {
                                        "K_x": [3000, 3000, 3000, 200, 200, 200]
                                        }
                                    }
    t = Task(robot, port)
    t.add_skill("hold","HoldPose",hold_context)
    t.start(queue=False)


def extract(robot, extractable, extractTo, container, port=12000):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "extraction.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["Container"] = container
    move_context["skill"]["objects"]["ExtractTo"] = extractTo
    move_context["skill"]["objects"]["Extractable"] = extractable
    move_context["skill"]["time_max"] = 10
    #move_context["user"]["env_X"] = [0, 0, 1, 1, 1, 1]
    t = Task(robot, port)
    t.add_skill("extraction","TaxExtraction",move_context)
    t.start(queue=False)
    return t.wait()

def insert(robot, insertable, approach, container, deltaX =[0,0,0,0,0,0], port=12000):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "insertion.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["Container"] = container
    move_context["skill"]["objects"]["Approach"] = approach
    move_context["skill"]["objects"]["Insertable"] = insertable
    move_context["skill"]["time_max"] = 7
    move_context["skill"]["p2"]["f_push"][2] = 25
    move_context["skill"]["p0"]["DeltaX"] = deltaX
    #move_context["user"]["env_X"] = [0, 0, 1, 1, 1, 1]
    t = Task(robot, port)
    t.add_skill("insertion","TaxInsertion",move_context)
    t.start(queue=False)
    return t.wait()

def insert2(robot, insertable, approach, container, deltaX =[0,0,0,0,0,0], port=12000):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "insertion2.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["Container"] = container
    move_context["skill"]["objects"]["Approach"] = approach
    move_context["skill"]["objects"]["Insertable"] = insertable
    move_context["skill"]["time_max"] = 6.5
    move_context["skill"]["p2"]["search_c"] = [0,0,20,0,0,0]
    move_context["skill"]["p2"]["search_a"] = [5,5,0,0,0,0]
    move_context["skill"]["p2"]["search_f"] = [0.75,1,0,0,0,0]
    move_context["skill"]["p2"]["delta_a"] = [.0,.0,0,0,0,0.1]
    move_context["skill"]["p2"]["delta_f"] = [0.75,0,0,0,0,0.5]
    move_context["skill"]["p2"]["t_d"] = 4
    move_context["skill"]["p2"]["K_X"] = [2000, 2000, 1000, 200, 200, 200],
    move_context["skill"]["p0"]["DeltaX"] = deltaX
    t = Task(robot, port)
    t.add_skill("insertion","Insertion2",move_context)
    t.start(queue=False)
    return t.wait()

def press_button(robot,tippable, approach):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "press_button.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["Button"] = tippable
    move_context["skill"]["objects"]["Approach"] = approach
    move_context["skill"]["condition_level_success"] = "Model"
    move_context["skill"]["condition_level_error"] = "Model"
    t = Task(robot)
    t.add_skill("press_button","TaxPressButton",move_context)
    t.start(queue=False)
    return t.wait()  


def update_object(robot, name, content={}):
    obj = call_method(robot,12000,"download_object_context",{"object":name})
    obj = obj["result"]["context"]
    for key, o in content.items():
        if key in obj:
            obj[key] = content[key]
    obj["object"] = obj["name"]
    call_method(robot,12000,"set_object",obj)


   
def _portal_result_or_raise(response, operation: str):
    result = response.get("result", {}) if isinstance(response, dict) else {}
    if not isinstance(result, dict) or result.get("result") is not True:
        error = ((result.get("error") or result.get("error_message"))
                 if isinstance(result, dict) else None) or "unknown Portal error"
        raise RuntimeError(f"{operation} failed: {error}")
    return response


def _require_idle_core(robot: str):
    response = call_method(robot, 12000, "get_state", {}, timeout=5)
    if response is None:
        raise RuntimeError(
            f"Core Portal at {robot}:12000 is unavailable or did not reply. "
            "Check the Core service logs and ensure "
            "MIOS_ENABLE_CORE_SCHEDULER=true; a running container alone "
            "does not mean the Portal is ready.")
    response = _portal_result_or_raise(response, "Read Core state")
    state = response["result"]
    if state.get("current_task") != "IdleTask":
        raise RuntimeError("Stop the previous teaching run with Ctrl+C before starting another run.")
    if state.get("error_message") or state.get("status") != "Idle":
        raise RuntimeError(f"Core is not idle and ready for teaching: {state.get('error_message') or state.get('status')}")


def _read_grasp_width(robot: str):
    response = _portal_result_or_raise(
        call_method(robot, 12000, "get_state", {}, timeout=5), "Read grasp opening")
    width = response["result"].get("gripper_width")
    if (type(width) not in (int, float) or not math.isfinite(width)
            or not 0 < width <= _MAX_GRASP_WIDTH):
        raise RuntimeError(
            f"Invalid grasp opening {width!r} m; keep the object supported.")
    return width


def _wait_for_grasp_width(robot: str):
    readings = []
    for _ in range(6):
        time.sleep(_GRASP_FEEDBACK_INTERVAL)
        readings.append(_read_grasp_width(robot))
        window = readings[-3:]
        if len(window) == 3 and max(window) - min(window) <= _GRASP_WIDTH_STABILITY:
            return window[-1]
    raise RuntimeError(
        "Gripper opening did not settle within six feedback checks; keep the object supported.")


def _detect_and_verify_grasp_width(robot: str):
    # The object width is unknown. Accept contact across the usable stroke
    # instead of demanding a nearly closed opening. Wait for settled feedback
    # before teach_object captures the width used by the later named grasp.
    detection = call_method(robot, 12000, "grasp", {
        "width": 0.0, "speed": TEACHING_GRASP_SPEED, "force": TEACHING_GRASP_FORCE,
        "epsilon_inner": 0.002, "epsilon_outer": _MAX_GRASP_WIDTH,
    }, timeout=30)
    try:
        _portal_result_or_raise(detection, "Contact-search grasp")
    except RuntimeError as error:
        raise RuntimeError(f"{error} Keep the object supported; no grasp pose was saved.") from error
    width = _wait_for_grasp_width(robot)
    print(f"Grasp command succeeded (requested force {TEACHING_GRASP_FORCE:g} N); "
          f"reported opening {width * 1000:.3f} mm.", flush=True)
    return width


def teach_insertion(robot: str, insertable: str, already_grasped: bool = False):
    """Teach poses, optionally keeping an object the operator has already grasped."""
    _require_idle_core(robot)
    _teach_insertion(robot, insertable, already_grasped)


def _teach_insertion(robot: str, insertable: str, already_grasped: bool = False):
    print("\nteaching ",insertable, "for ", robot,"\n")
    if already_grasped:
        handguiding(
            robot,
            "Keep the object grasped and hand-guide to the grasp pose. "
            "Confirm the object is securely held. [Press Enter to save]")
        response = _portal_result_or_raise(
            call_method(robot, 12000, "get_state", {}, timeout=5), "Read existing grasp opening")
        width = response["result"].get("gripper_width")
        if type(width) not in (int, float) or not math.isfinite(width) or width <= 0:
            raise RuntimeError(f"Invalid existing grasp opening {width!r} m; no grasp pose was saved.")
        if width > 0.08:
            raise RuntimeError(
                f"Reported gripper opening is {width * 1000:.2f} mm, above the 80 mm accepted for an existing grasp. "
                "already_grasped=True skips closing the fingers. For open fingers, use "
                "already_grasped=False to place and grasp the object at the prompt. No grasp pose was saved."
            )
        # The operator confirms contact; an encoder reading alone cannot
        # distinguish a thin object from an almost closed empty gripper.
        print(f"Keeping the confirmed grasp (reported opening {width * 1000:.3f} mm).", flush=True)
    else:
        handguiding(
            robot,
            "Insert the object into the open robot fingers, then clear your fingers from the closing path. "
            "[Press Enter to close the gripper]")
        print("Closing the gripper until object contact is detected...", flush=True)
        width = _detect_and_verify_grasp_width(robot)

    # The deployed Portal handler reads the legacy ``width`` spelling.
    print("Saving the grasp pose...", flush=True)
    _portal_result_or_raise(
        call_method(robot, 12000, "teach_object", {
            "object": insertable, "width": True, "force": TEACHING_GRASP_FORCE}),
        "Teach grasp pose",
    )
    
    handguiding(robot, "Teach approach pose slightly above the object\'s container. [Press any key to continue]")
    _portal_result_or_raise(
        call_method(robot, 12000, "teach_object", {"object": insertable+"_container_approach"}),
        "Teach container approach",
    )
    handguiding(robot, "Teach container pose with the object fully inserted into the container. [Press any key to continue]")
    _portal_result_or_raise(
        call_method(robot, 12000, "teach_object", {"object": insertable+"_container"}),
        "Teach container pose",
    )
    handguiding(robot, "Extract robot and object again. [Press any key to continue]")

def handguiding(robot: str, message: str = "Press any key to stop"):
    """Run a Portal task; Core owns the ROS controller lifecycle."""
    context = {
        "skill": {
            "record_trajectory": False,
            #"recording_length": 1,
            #"recording_name": None,

        },
        "control": {
            "control_mode": 0
        }
    }
    _require_idle_core(robot)
    t = Task(robot)
    t.add_skill("record_trajectory", "HandGuiding", context)
    try:
        t.start()
        _wait_for_handguiding_control(robot)
        try:
            input(message)
        except (KeyboardInterrupt, EOFError) as error:
            print("\nHandGuiding input interrupted; stopping task.")
            raise RuntimeError("HandGuiding teaching was interrupted before confirmation.") from error
    finally:
        if t._start_attempted:
            # A lost start reply may still have started a task on Core.
            result = t.stop()
            print("Result: " + str(result))
            _portal_result_or_raise(result, "Stop HandGuiding")
            _wait_for_handguiding_stop(robot)
    return result


def _wait_for_handguiding_control(robot: str):
    """A queued task UUID alone does not confirm that Core acquired the arm."""
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        response = _portal_result_or_raise(
            call_method(robot, 12000, "get_state", {}, timeout=5),
            "Wait for HandGuiding control")
        state = response["result"]
        if "control_active" not in state:
            raise RuntimeError("Core does not report controller readiness; rebuild the Core image before teaching.")
        if state.get("error_message") or state.get("status") not in ("Idle", "Move"):
            raise RuntimeError(f"HandGuiding is not ready: {state.get('error_message') or state.get('status')}")
        if state.get("current_task") == "GenericTask" and state["control_active"] is True:
            return
        time.sleep(0.1)
    raise RuntimeError("Core did not acquire HandGuiding control within 20 seconds. Check the Core and Control service logs.")


def _wait_for_handguiding_stop(robot: str):
    """Do not save a pose or start the next stage until Core has released control."""
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        response = _portal_result_or_raise(
            call_method(robot, 12000, "get_state", {}, timeout=5), "Wait for HandGuiding stop")
        state = response["result"]
        if (state.get("current_task") == "IdleTask" and state.get("control_active") is False
                and state.get("status") == "Idle" and not state.get("error_message")):
            return
        time.sleep(0.1)
    raise RuntimeError("Core did not return to idle after stopping HandGuiding. Check the Core and Control service logs.")


if __name__ == "__main__":
    # False starts a new grasp from open fingers. Use True to resume teaching
    # with an object that is already securely held, without closing again.
    call_method("127.0.0.1", 12000, "release_object",{"width": 0.08, "speed": 0.2})
    call_method("127.0.0.1", 12000, "home_gripper")
    # handguiding("127.0.0.1")
    # teach_insertion("127.0.0.1", "janinetest1", already_grasped=False)
