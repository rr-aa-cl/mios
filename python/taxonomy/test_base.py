import abc
from abc import ABC
import os
import random


class BaseTest(ABC):

    def __init__(self, robot: str, skill_class: str):
        self.db_host = "collective-control-001"
        self.db = "taxonomy"
        self.robot = robot
        self.path_to_default_context = os.getcwd() + "/default_contexts/"
        self.skill_class = skill_class
        self.default_context = dict()
        self.reset_default_contexts = dict()
        self.object_modifier = dict()
        self.record_performance = False

    def initialize(self, default_context: dict, reset_default_contexts: dict, record_performance: bool = True,
                   object_modifier: dict = {}):
        self.default_context = default_context
        self.reset_default_contexts = reset_default_contexts
        self.record_performance = record_performance
        self.object_modifier = object_modifier

    def apply_object_modifiers(self, context):
        print("#################################MOD########################")
        valid_modifiers = {"O_T_OB", "T_T_OB"}
        for skill in self.object_modifier:
            if skill not in context["skills"]:
                print("Skill " + skill + " not in object modifier list.")
                return False
            object_modifier = dict()
            if "objects_modifier" not in context["skills"][skill]["skill"]:
                context["skills"][skill]["skill"]["objects_modifier"] = dict()
            for obj in self.object_modifier[skill]:
                if obj not in context["skills"][skill]["skill"]["objects"]:
                    print("Skill " + skill + " has no object " + obj + " to modify.")
                    return False
                object_modifier[obj] = dict()
                if obj not in context["skills"][skill]["skill"]["objects_modifier"]:
                    context["skills"][skill]["skill"]["objects_modifier"][obj] = dict()
                for modifier in self.object_modifier[skill][obj]:
                    if modifier not in valid_modifiers:
                        print(modifier + " is not a valid object modifier.")
                        return False
                    if modifier == "T_T_OB" or modifier == "O_T_OB":
                        x = 0
                        y = 0
                        z = 0
                        if "x" in self.object_modifier[skill][obj][modifier]:
                            x = random.uniform(self.object_modifier[skill][obj][modifier]["x"][0],
                                               self.object_modifier[skill][obj][modifier]["x"][1])
                        if "y" in self.object_modifier[skill][obj][modifier]:
                            y = random.uniform(self.object_modifier[skill][obj][modifier]["y"][0],
                                               self.object_modifier[skill][obj][modifier]["y"][1])
                        if "z" in self.object_modifier[skill][obj][modifier]:
                            z = random.uniform(self.object_modifier[skill][obj][modifier]["z"][0],
                                               self.object_modifier[skill][obj][modifier]["z"][1])
                        mod_value = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1]
                    context["skills"][skill]["skill"]["objects_modifier"][obj][modifier] = mod_value
            print(context["skills"][skill]["skill"]["objects_modifier"])

    @abc.abstractmethod
    def run(self, args: dict, cost_function: str, result_uuid: str = None, result_trial: int = None):
        raise NotImplementedError

    @abc.abstractmethod
    def reset(self, args: dict):
        raise NotImplementedError

    @abc.abstractmethod
    def teach(self, args: dict):
        raise NotImplementedError


def start_experiment(skill_test: BaseTest, run_args: dict, reset_args: dict, n_iter: int, cost_function:str,
                     result_id: str = None, result_trial: int = None):
    for i in range(n_iter):
        print("Running iteration " + str(i))
        skill_test.run(run_args, cost_function, result_id, result_trial)
        skill_test.reset(reset_args)
