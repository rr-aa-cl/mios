from test_base import BaseTest
from taxonomy_utils import *
import json
from xmlrpc.client import ServerProxy


class InsertionTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "insertion")
        f = open(self.path_to_default_context + "insertion.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "extraction.json")
        reset_default_contexts["extraction"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)

        object_modifier = {
            "insertion": {
                "Approach": {
                    "T_T_OB": {
                        "x": (-0.003, 0.003),
                        "y": (-0.003, 0.003)
                    }
                },
                "Container": {
                    "T_T_OB": {
                        "x": (-0.003, 0.003),
                        "y": (-0.003, 0.003)
                    }
                }
            }
        }

        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Insertable"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Insertable": args["Insertable"],
            "Container": args["Container"],
            "Approach": args["Approach"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxInsertion", context)
        self.apply_object_modifiers(t.context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Insertable"], cost_function, result)

    def reset(self, args: dict):
        # call_method(self.robot, 12000, "set_grasped_object", {"object": args["Extractable"]})
        t = Task(self.robot)
        context = self.reset_default_contexts["extraction"]
        context["skill"]["objects"] = {
            "Extractable": args["Extractable"],
            "Container": args["Container"],
            "ExtractTo": args["ExtractTo"]
        }
        t.add_skill("extraction", "TaxExtraction", context)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        teach_object(self.robot, args["Insertable"])
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Insertable"]})
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the container pose.")
        teach_object(self.robot, args["Container"])


class ExtractionTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "extraction")
        f = open(self.path_to_default_context + "extraction.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "insertion.json")
        reset_default_contexts["insertion"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Extractable"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Extractable": args["Extractable"],
            "Container": args["Container"],
            "ExtractTo": args["ExtractTo"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxExtraction", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Extractable"], cost_function, result)

    def reset(self, args: dict):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Insertable"]})
        t = Task(self.robot)
        print(self.reset_default_contexts)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        context = self.reset_default_contexts["insertion"]
        context["skill"]["objects"] = {
            "Insertable": args["Insertable"],
            "Container": args["Container"],
            "Approach": args["Approach"]
        }
        t.add_skill("insertion", "TaxInsertion", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        teach_object(self.robot, args["Extractable"])
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Extractable"]})
        input("Press enter to teach the retreat pose.")
        teach_object(self.robot, args["ExtractTo"])
        input("Press enter to teach the container pose.")
        teach_object(self.robot, args["Container"])


class PushSurfaceTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "push_surface")
        f = open(self.path_to_default_context + "push_surface.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Surface": args["Surface"],
            "Approach": args["Approach"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxPush", context)
        t.start()
        result = t.wait()
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Surface"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the surface pose.")
        teach_object(self.robot, args["Surface"])


class PressButtonTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "press_button")
        f = open(self.path_to_default_context + "press_button.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        s = ServerProxy("http://collective-control-001:8000", allow_none=True)
        s.subscribe_to_event("button_press", self.robot, "12000")
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Button": args["Button"],
            "Approach": args["Approach"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxPressButton", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Button"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the pressed button pose.")
        teach_object(self.robot, args["Button"])


class SlideObjectTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "slide_object")
        f = open(self.path_to_default_context + "slide_object.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_cart.json")
        reset_default_contexts["move_up"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        f = open(self.path_to_default_context + "move_contact.json")
        reset_default_contexts["move_contact"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Slidable"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Surface": args["Surface"],
            "Slidable": args["Slidable"],
            "GoalPose": args["GoalPose"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxSlideObject", context)
        t.start()
        result = t.wait()

        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Slidable"], cost_function, result)

    def reset(self, args: dict):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Slidable"]})
        t = Task(self.robot)
        context = self.reset_default_contexts["move_up"]
        context["skill"]["objects"]["GoalPose"] = "EndEffector"
        context["skill"]["p0"]["T_T_EE_g_offset"] = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0.05, 1]
        t.add_skill("move_up", "TaxMove", context)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        context = self.reset_default_contexts["move_contact"]
        context["skill"]["objects"]["goal_pose"] = args["Surface"]
        t.add_skill("move_contact", "MoveToContact", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the slidable.")
        teach_object(self.robot, args["Slidable"])
        input("Press enter to teach the surface.")
        teach_object(self.robot, args["Surface"])
        input("Press enter to teach the goal pose.")
        teach_object(self.robot, args["GoalPose"])


class TipTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "tip")
        f = open(self.path_to_default_context + "tip.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def pre_run(self):
        s = ServerProxy("http://collective-control-001:8000", allow_none=True)
        s.subscribe_to_event("tippable_pressed", "collective-panda-007", "12000")

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):

        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Tippable": args["Tippable"],
            "Approach": args["Approach"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxTip", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Tippable"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the tipped pose.")
        teach_object(self.robot, args["Tippable"])


class GrabTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "grab")
        f = open(self.path_to_default_context + "grab.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "place.json")
        reset_default_contexts["place"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Grabbable": args["Grabbable"],
            "Approach": args["Approach"],
            "Retract": args["Retract"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxGrab", context)
        t.start()
        result = t.wait()
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Grabbable"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["place"]
        context["skill"]["objects"]["Placeable"] = args["Placeable"]
        context["skill"]["objects"]["Surface"] = args["Placeable"]
        context["skill"]["objects"]["Approach"] = args["Approach"]
        context["skill"]["objects"]["Retract"] = args["Retract"]
        t.add_skill("place", "TaxPlace", context)
        context = self.reset_default_contexts["move"]
        context["skill"]["objects"]["goal_pose"] = args["Retract"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the grabbable.")
        teach_object(self.robot, args["Grabbable"])
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the retract pose.")
        teach_object(self.robot, args["Retract"])


class PlaceTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "place")
        f = open(self.path_to_default_context + "place.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "grab.json")
        reset_default_contexts["grab"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Placeable"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Placeable": args["Placeable"],
            "Surface": args["Surface"],
            "Approach": args["Approach"],
            "Retract": args["Retract"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxPlace", context)
        t.start()
        result = t.wait()
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Placeable"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["grab"]
        context["skill"]["objects"]["Grabbable"] = args["Grabbable"]
        context["skill"]["objects"]["Approach"] = args["Approach"]
        context["skill"]["objects"]["Retract"] = args["Retract"]
        t.add_skill("grab", "TaxGrab", context)
        context = self.reset_default_contexts["move"]
        context["skill"]["objects"]["goal_pose"] = args["Retract"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the grabbable.")
        teach_object(self.robot, args["Placeable"])
        input("Press enter to teach the surface.")
        teach_object(self.robot, args["Surface"])
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the retract pose.")
        teach_object(self.robot, args["Retract"])


class CarryTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "carry")
        f = open(self.path_to_default_context + "carry.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, result_uuid: str = None, result_trial: int = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Carriable"]})
        context = self.default_context
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)
        context["skill"]["objects"] = {
            "Carriable": args["Carriable"],
            "GoalPose": args["GoalPose"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxCarry", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Carriable"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the carriable.")
        teach_object(self.robot, args["Carriable"])
        input("Press enter to teach the start pose.")
        teach_object(self.robot, args["StartPose"])
        input("Press enter to teach the goal pose.")
        teach_object(self.robot, args["GoalPose"])


class MoveTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "move")
        f = open(self.path_to_default_context + "move_cart.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "GoalPose": args["GoalPose"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxMove", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["GoalPose"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the start pose.")
        teach_object(self.robot, args["StartPose"])
        input("Press enter to teach the goal pose.")
        teach_object(self.robot, args["GoalPose"])


class DragTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "drag")
        f = open(self.path_to_default_context + "drag.json")
        default_context = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts = dict()
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Draggable"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Draggable": args["Draggable"],
            "GoalPose": args["GoalPose"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxDrag", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Draggable"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the draggable.")
        teach_object(self.robot, args["Draggable"])
        input("Press enter to teach the goal pose.")
        teach_object(self.robot, args["GoalPose"])


class ShoveTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "shove")
        f = open(self.path_to_default_context + "shove.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Shovable": args["Shovable"],
            "Approach": args["Approach"],
            "Direction": args["Direction"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxShove", context)
        t.start()
        result = t.wait()
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Shovable"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()
        input("Press enter to continue")

    def teach(self, args: dict):
        input("Press enter to teach the shovable.")
        teach_object(self.robot, args["Shovable"])
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the direction.")
        teach_object(self.robot, args["Direction"])


class TurnTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "turn")
        f = open(self.path_to_default_context + "turn.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "turn.json")
        reset_default_contexts["turn_back"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Turnable"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Turnable": args["Turnable"],
            "GoalOrientation": args["GoalOrientation"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxTurn", context)
        t.start()
        result = t.wait()
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Turnable"], cost_function, result)

    def reset(self, args: dict):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Turnable"]})
        t = Task(self.robot)
        context = self.reset_default_contexts["turn_back"]
        context["skill"]["objects"] = {
            "Turnable": args["Turnable"],
            "GoalOrientation": args["GoalOrientation"]
        }
        context["skill"]["p0"]["dX_d"] = [0.1, 0.5]
        context["skill"]["p0"]["ddX_d"] = [0.1, 1]
        t.add_skill("turn_back", "TaxTurn", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the turnable.")
        teach_object(self.robot, args["Turnable"])
        input("Press enter to teach the goal orientation.")
        teach_object(self.robot, args["GoalOrientation"])


class IndentationTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "indentation")
        f = open(self.path_to_default_context + "indentation.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, result_uuid: str = None, result_trial: int = None):
        context = self.default_context
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)
        context["skill"]["objects"] = {
            "Surface": args["Surface"],
            "Approach": args["Approach"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxIndentation", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Surface"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move"]
        context["skill"]["objects"]["goal_pose"] = args["goal_pose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the Surface.")
        teach_object(self.robot, args["Surface"])
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])


class SlideOpenTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "slide_open")
        f = open(self.path_to_default_context + "slide_open.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_cart.json")
        reset_default_contexts["move_up"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Container": args["Container"],
            "Approach": args["Approach"],
            "GoalPose": args["GoalPose"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxSlideOpen", context)
        t.start()
        result = t.wait()

        ask_for_result(result)
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Container"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move_up"]
        context["skill"]["objects"]["GoalPose"] = "EndEffector"
        context["skill"]["p0"]["T_T_EE_g_offset"] = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0.05, 1]
        t.add_skill("move_up", "TaxMove", context)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["Approach"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()
        input("Press enter to continue")

    def teach(self, args: dict):
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the container.")
        teach_object(self.robot, args["Container"])
        input("Press enter to teach the goal pose.")
        teach_object(self.robot, args["GoalPose"])


class WipeTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "wipe")
        f = open(self.path_to_default_context + "wipe.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_cart.json")
        reset_default_contexts["move_up"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, cost_function: str, result_uuid: str = None, result_trial: int = None):
        context = self.default_context
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)
        context["skill"]["objects"] = {
            "Wipeable": args["Wipeable"],
            "Approach": args["Approach"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxWipe", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Wipeable"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move_joint"]
        context["skill"]["objects"]["goal_pose"] = args["GoalPose"]
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()
        input("Press enter to continue")

    def teach(self, args: dict):
        input("Press enter to teach the wipeable.")
        teach_object(self.robot, args["Wipeable"])
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])


class SwipeTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "swipe")
        f = open(self.path_to_default_context + "swipe.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "swipe.json")
        reset_default_contexts["swipe"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Stylus"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "SwipeStart": args["SwipeStart"],
            "SwipeEnd": args["SwipeEnd"],
            "Approach": args["Approach"],
            "Retract": args["Retract"],
            "Stylus": args["Stylus"],
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxSwipe", context)
        t.start()
        result = t.wait()

        ask_for_result(result)
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Stylus"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["swipe"]
        context["skill"]["objects"] = {
            "SwipeStart": args["SwipeStart"],
            "SwipeEnd": args["SwipeEnd"],
            "Approach": args["Approach"],
            "Retract": args["Retract"],
            "Stylus": args["Stylus"],
        }
        t.add_skill("swipe", "TaxSwipe", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Stylus"]})
        input("Press enter to teach the stylus.")
        teach_object(self.robot, args["Stylus"])
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the swipe start.")
        teach_object(self.robot, args["SwipeStart"])
        input("Press enter to teach the swipe end.")
        teach_object(self.robot, args["SwipeEnd"])
        input("Press enter to teach the retract pose.")
        teach_object(self.robot, args["Retract"])


class WrenchTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "wrench")
        f = open(self.path_to_default_context + "wrench.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, result_uuid: str = None, result_trial: int = None):
        context = self.default_context
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)
        context["skill"]["objects"] = {
            "Wrench": args["Wrench"],
            "GoalPose": args["GoalPose"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxWrench", context)
        t.start()
        result = t.wait()

        ask_for_result(result)

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Wrench"], cost_function, result)

    def reset(self, args: dict):
        input("Press Enter to continue...")

    def teach(self, args: dict):
        input("Press enter to teach the wrench.")
        teach_object(self.robot, args["Wrench"])
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Wrench"]})
        input("Press enter to teach the goal pose.")
        teach_object(self.robot, args["GoalPose"])


class TurnLeverTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "turn_lever")
        f = open(self.path_to_default_context + "turn_lever.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "turn_lever.json")
        reset_default_contexts["turn_back"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Lever"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Lever": args["Lever"],
            "GoalPosition": args["GoalPosition"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxTurnLever", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Lever"], cost_function, result)

    def reset(self, args: dict):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Lever"]})
        t = Task(self.robot)
        context = self.reset_default_contexts["turn_back"]
        context["skill"]["objects"] = {
            "Lever": args["Lever"],
            "GoalPosition": args["GoalPosition"]
        }
        context["skill"]["p0"]["dX_d"] = [0.1, 0.5]
        context["skill"]["p0"]["ddX_d"] = [0.1, 1]
        t.add_skill("turn_back", "TaxTurnLever", context)
        context = self.reset_default_contexts["move"]
        context["skill"]["objects"] = {
            "goal_pose": args["GoalPosition"]
        }
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the lever.")
        teach_object(self.robot, args["Lever"])
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Lever"]})
        input("Press enter to teach the start pose.")
        teach_object(self.robot, args["StartPose"])
        input("Press enter to teach the goal position.")
        teach_object(self.robot, args["GoalPosition"])


class CutTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "cut")
        f = open(self.path_to_default_context + "cut.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Knife"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "CutStart": args["CutStart"],
            "CutEnd": args["CutEnd"],
            "Approach": args["Approach"],
            "Retract": args["Retract"],
            "Knife": args["Knife"],
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxCut", context)
        t.start()
        result = t.wait()

        ask_for_result(result)
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Knife"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move"]
        context["skill"]["objects"] = {
            "goal_pose": args["Approach"]
        }
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the knife.")
        teach_object(self.robot, args["Knife"])
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Knife"]})
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the cut start.")
        teach_object(self.robot, args["CutStart"])
        input("Press enter to teach the cut end.")
        teach_object(self.robot, args["CutEnd"])
        input("Press enter to teach the retract pose.")
        teach_object(self.robot, args["Retract"])


class DisplaceTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "displace")
        f = open(self.path_to_default_context + "displace.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "displace.json")
        reset_default_contexts["displace"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, result_uuid: str = None, result_trial: int = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Displaceable"]})
        context = self.default_context
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)
        context["skill"]["objects"] = {
            "Displaceable": args["Displaceable"],
            "GoalPose": args["GoalPose"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxDisplace", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Displaceable"], cost_function, result)

    def reset(self, args: dict):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Displaceable"]})
        t = Task(self.robot)
        context = self.reset_default_contexts["displace"]
        context["skill"]["objects"] = {
            "Displaceable": args["Displaceable"],
            "GoalPose": args["GoalPose"]
        }
        context["skill"]["p0"]["dX_d"] = [0.1, 0.5]
        context["skill"]["p0"]["ddX_d"] = [0.1, 1]
        t.add_skill("displace", "TaxDisplace", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the displaceable.")
        teach_object(self.robot, args["Displaceable"])
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Displaceable"]})
        input("Press enter to teach the start pose.")
        teach_object(self.robot, args["StartPose"])
        input("Press enter to teach the goal pose.")
        teach_object(self.robot, args["GoalPose"])


class ScrewTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "screw")
        f = open(self.path_to_default_context + "screw.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12002, "set_grasped_object", {"object": args["Screwdriver"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Screw": args["Screw"],
            "Approach": args["Approach"],
            "Screwdriver": args["Screwdriver"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxScrew", context)
        t.start()
        result = t.wait()
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Screw"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move"]
        context["skill"]["objects"] = {
            "goal_pose": args["Approach"]
        }
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()
        input("Press enter to continue.")

    def teach(self, args: dict):
        call_method(self.robot, 12002, "set_grasped_object", {"object": args["Screwdriver"]})
        input("Press enter to teach the screwdriver.")
        teach_object(self.robot, args["Screwdriver"])
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the screw pose.")
        teach_object(self.robot, args["Screw"])


class ScrewOutTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "screw_out")
        f = open(self.path_to_default_context + "screw_out.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12002, "set_grasped_object", {"object": args["Screwdriver"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Screw": args["Screw"],
            "Approach": args["Approach"],
            "Screwdriver": args["Screwdriver"],
            "GoalPosition": args["GoalPosition"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxScrewOut", context)
        t.start()
        result = t.wait()
        print(result["result"]["task_result"]["skill_results"][self.skill_class]["cost"][cost_function])

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Screw"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move"]
        context["skill"]["objects"] = {
            "goal_pose": args["Retract"]
        }
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()
        input("Press enter to continue.")

    def teach(self, args: dict):
        input("Press enter to teach the screwdriver.")
        teach_object(self.robot, args["Screwdriver"])
        call_method(self.robot, 12002, "set_grasped_object", {"object": args["Screwdriver"]})
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the screw pose.")
        teach_object(self.robot, args["Screw"])
        input("Press enter to teach the goal position.")
        teach_object(self.robot, args["GoalPosition"])
        input("Press enter to teach the retract pose.")
        teach_object(self.robot, args["Retract"])


class HammerTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "hammer")
        f = open(self.path_to_default_context + "hammer.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, result_uuid: str = None, result_trial: int = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Hammer"]})
        context = self.default_context
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)
        context["skill"]["objects"] = {
            "Hammer": args["Hammer"],
            "Approach": args["Approach"],
            "Hammerable": args["Hammerable"],
            "GoalPosition": args["GoalPosition"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxHammer", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Hammerable"], cost_function, result)

    def reset(self, args: dict):
        t = Task(self.robot)
        context = self.reset_default_contexts["move"]
        context["skill"]["objects"] = {
            "goal_pose": args["Approach"]
        }
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the hammer.")
        teach_object(self.robot, args["Hammer"])
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Hammer"]})
        input("Press enter to teach the approach pose.")
        teach_object(self.robot, args["Approach"])
        input("Press enter to teach the goal position.")
        teach_object(self.robot, args["GoalPosition"])
        input("Press enter to teach the hammerable.")
        teach_object(self.robot, args["Hammerable"])


class BendTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "bend")
        f = open(self.path_to_default_context + "bend.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "bend.json")
        reset_default_contexts["bend"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance=record_performance)

    def run(self, args: dict, cost_function: str, host: str = None, database: str = None, task: str = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Bendable"]})
        context = self.default_context
        if host is not None and database is not None and task is not None:
            context = download_result2(host, database, self.skill_class, task, cost_function)
        context["skill"]["objects"] = {
            "Bendable": args["Bendable"],
            "GoalPose": args["GoalPose"]
        }

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxBend", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Bendable"], cost_function, result)

    def reset(self, args: dict):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Bendable"]})
        t = Task(self.robot)
        context = self.reset_default_contexts["bend"]
        context["skill"]["objects"] = {
            "Bendable": args["Bendable"],
            "GoalPose": args["GoalPose"]
        }
        context["skill"]["p0"]["dX_d"] = [0.1, 0.5]
        context["skill"]["p0"]["ddX_d"] = [0.1, 1]
        t.add_skill("bend", "TaxBend", context)
        context = self.reset_default_contexts["move"]
        context["skill"]["objects"] = {
            "goal_pose": args["GoalPose"]
        }
        t.add_skill("move", "MoveToPoseJoint", context)
        t.start()
        t.wait()

    def teach(self, args: dict):
        input("Press enter to teach the bendable.")
        teach_object(self.robot, args["Bendable"])
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Bendable"]})
        input("Press enter to teach the start pose.")
        teach_object(self.robot, args["StartPose"])
        input("Press enter to teach the goal pose.")
        teach_object(self.robot, args["GoalPose"])