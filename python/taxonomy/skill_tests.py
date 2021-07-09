from test_base import BaseTest
from taxonomy_utils import *
import json


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
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, result_uuid: str = None, result_trial: int = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Insertable"]})
        context = self.default_context
        context["skill"]["objects"] = {
            "Insertable": args["Insertable"],
            "Container": args["Container"],
            "Approach": args["Approach"]
        }
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxInsertion", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Insertable"], result)

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
        reset_default_contexts["extraction"] = json.load(f)
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, result_uuid: str = None, result_trial: int = None):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Extractable"]})
        context = self.default_context
        context["skill"]["objects"] = {
            "Extractable": args["Extractable"],
            "Container": args["Container"],
            "ExtractTo": args["ExtractTo"]
        }
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxExtraction", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Extractable"], result)

    def reset(self, args: dict):
        call_method(self.robot, 12000, "set_grasped_object", {"object": args["Insertable"]})
        t = Task(self.robot)
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


class PushTest(BaseTest):
    def __init__(self, robot: str, record_performance: bool = True):
        super().__init__(robot, "push")
        f = open(self.path_to_default_context + "push.json")
        default_context = json.load(f)
        reset_default_contexts = dict()
        f = open(self.path_to_default_context + "move_joint.json")
        reset_default_contexts["move_joint"] = json.load(f)
        self.initialize(default_context, reset_default_contexts, record_performance)

    def run(self, args: dict, result_uuid: str = None, result_trial: int = None):
        context = self.default_context
        context["skill"]["objects"] = {
            "Surface": args["Surface"],
            "Approach": args["Approach"]
        }
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxPush", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Surface"], result)

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

    def run(self, args: dict, result_uuid: str = None, result_trial: int = None):
        context = self.default_context
        context["skill"]["objects"] = {
            "Button": args["Button"],
            "Approach": args["Approach"]
        }
        if result_uuid is not None and result_trial is not None:
            context = download_result(self.robot, "ml_results", self.skill_class, result_uuid, result_trial)

        t = Task(self.robot)
        t.add_skill(self.skill_class, "TaxPressButton", context)
        t.start()
        result = t.wait()

        if self.record_performance is True:
            upload_result(self.db_host, self.skill_class, args["Button"], result)

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
