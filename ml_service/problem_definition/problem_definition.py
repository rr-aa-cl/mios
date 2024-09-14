from typing import Optional
from problem_definition.domain import Domain
from engine.task_result import TaskResult
from engine.task_result import QMetric
from engine.task_result import cost_types
from utils.exception import CostFunctionError
import logging
import numpy as np
import random

logger = logging.getLogger("ml_service")


class CostFunction:
    def __init__(self):
        self.optimum_skills = []
        self.optimum_weights = dict.fromkeys(cost_types, 0)
        self.optimum_expressions = dict.fromkeys(cost_types, "var")
        self.max_cost = dict.fromkeys(cost_types, 1)
        self.heuristic_skills = []
        self.heuristic_expressions = "var"
        self.finish_thr = 1  # finsih threshold states how often optimal_thr needs to be undercut to finish
        self.normal_cost = 1

    def to_dict(self):
        c = {
            "optimum_skills": self.optimum_skills,
            "optimum_weights": self.optimum_weights,
            "optimum_expressions": self.optimum_expressions,
            "heuristic_skills": self.heuristic_skills,
            "heuristic_expressions": self.heuristic_expressions,
            "max_cost": self.max_cost,
            "finish_thr": self.finish_thr
        }
        return c

    @staticmethod
    def from_dict(cf_dict: dict):
        c = CostFunction()
        c.optimum_skills = cf_dict["optimum_skills"]
        c.optimum_weights = cf_dict["optimum_weights"]
        c.optimum_expressions = cf_dict["optimum_expressions"]
        c.heuristic_skills = cf_dict["heuristic_skills"]
        c.heuristic_expressions = cf_dict["heuristic_expressions"]
        c.max_cost = cf_dict["max_cost"]
        c.finish_thr = cf_dict["finish_thr"]
        return c


class ProblemDefinition:
    def __init__(self, skill_class: str, skill_instance: str, domain: Domain, default_context: dict,
                 setup_instructions: list, termination_instruction: list, reset_instruction: list,
                 cost_function: CostFunction, identity: list, identity_weights: list = None, tags=None,
                 object_modifier: dict = {}, n_variations = 1, optimum_threshold:float = 0, host:str=None, variate_only_success:bool=False):
        if tags is None:
            tags = []
        self.host = host
        self.domain = domain
        self.object_modifier = object_modifier
        self.default_context = default_context
        self.setup_instructions = setup_instructions
        self.termination_instructions = termination_instruction
        self.reset_instructions = reset_instruction
        self.uuid = "INVALID"
        self.skill_class = skill_class
        self.skill_instance = skill_instance
        self.cost_function = cost_function
        self.tags = tags
        self.optimum_thr = optimum_threshold
        self.n_variations = n_variations
        self.variate_only_success = variate_only_success  # with an empty object_modifier this can be used to repeat successfull trials for n_variations
        if identity is None:
            self.identity = [0]
        else:
            self.identity = identity
        if identity_weights is None:
            self.identity_weights = [1] * len(self.identity)
        else:
            self.identity_weights = identity_weights

        if len(self.identity) != len(self.identity_weights):
            logger.debug(str(len(self.identity)) + "!=" + str(len(self.identity_weights)))
            raise CostFunctionError

    def self_check(self):
        healthy = True
        if self.domain.self_check() is False:
            healthy = False

        return healthy

    def get_task_identifier(self) -> dict:
        return {"skill_class": self.skill_class, "tags": self.tags, "identity": self.identity,"skill_instance":self.skill_instance}

    def get_identification_name(self) -> str:
        return str(self.get_task_identifier())

    def to_dict(self) -> dict:
        problem_definition = {
            "domain": self.domain.to_dict(),
            "default_context": self.default_context,
            "setup_instructions": self.setup_instructions,
            "termination_instructions": self.termination_instructions,
            "reset_instructions": self.reset_instructions,
            "uuid": self.uuid,
            "skill_class": self.skill_class,
            "tags": self.tags,
            "cost_function": self.cost_function.to_dict(),
            "optimum_thr": self.optimum_thr,
            "skill_instance": self.skill_instance,
            "identity": self.identity,
            "identity_weights": self.identity_weights,
            "object_modifier": self.object_modifier,
            "n_variations": self.n_variations,
            "optimum_threshold": self.optimum_thr,
            "variate_only_success": self.variate_only_success
        }
        return problem_definition

    @staticmethod
    def from_dict(pd_dict):
        pd = ProblemDefinition(pd_dict["skill_class"], pd_dict["skill_instance"], Domain.from_dict(pd_dict["domain"]),
                               pd_dict["default_context"], pd_dict["setup_instructions"],
                               pd_dict["termination_instructions"], pd_dict["reset_instructions"],
                               CostFunction.from_dict(pd_dict["cost_function"]), pd_dict["identity"],
                               pd_dict["identity_weights"], pd_dict["tags"], object_modifier=pd_dict["object_modifier"],
                               n_variations=pd_dict["n_variations"],optimum_threshold=pd_dict["optimum_threshold"],
                               variate_only_success=pd_dict["variate_only_success"])
        pd.domain = Domain.from_dict(pd_dict["domain"])
        pd.cost_function = CostFunction.from_dict(pd_dict["cost_function"])
        return pd

    def is_valid(self) -> bool:
        valid = True
        for i in range(len(self.setup_instructions)):
            if "method" not in self.setup_instructions[i]:
                logger.error("Setup instruction " + str(i) + " is missing a method.")
                valid = False
            if "parameters" not in self.setup_instructions[i]:
                logger.error("Setup instruction " + str(i) + " is missing parameters.")
                valid = False
        for i in range(len(self.termination_instructions)):
            if "method" not in self.termination_instructions[i]:
                logger.error("Termination instruction " + str(i) + " is missing a method.")
                valid = False
            if "parameters" not in self.termination_instructions[i]:
                logger.error("Termination instruction " + str(i) + " is missing parameters.")
                valid = False
        for i in range(len(self.reset_instructions)):
            if "method" not in self.reset_instructions[i]:
                logger.error("Reset instruction " + str(i) + " is missing a method.")
                valid = False
            if "parameters" not in self.reset_instructions[i]:
                logger.error("Reset instruction " + str(i) + " is missing parameters.")
                valid = False

        return valid

    def apply_object_modifiers(self, context):
        print("#################################MOD########################")
        valid_modifiers = {"O_T_OB", "T_T_OB"}
        for skill in self.object_modifier:
            if skill not in context["skills"]:
                logger.error("Skill " + skill + " not in object modifier list.")
                return False
            object_modifier = dict()
            if "objects_modifier" not in context["skills"][skill]["skill"]:
                context["skills"][skill]["skill"]["objects_modifier"] = dict()
            for obj in self.object_modifier[skill]:
                if obj not in context["skills"][skill]["skill"]["objects"]:
                    logger.error("Skill " + skill + " has no object " + obj + " to modify.")
                    return False
                object_modifier[obj] = dict()
                if obj not in context["skills"][skill]["skill"]["objects_modifier"]:
                    context["skills"][skill]["skill"]["objects_modifier"][obj] = dict()
                for modifier in self.object_modifier[skill][obj]:
                    if modifier == "linked_objects":
                        continue
                    if modifier not in valid_modifiers:
                        logger.error(modifier + " is not a valid object modifier.")
                        return False
                    if "linked_objects" in self.object_modifier[skill][obj]:
                        for lo in self.object_modifier[skill][obj]["linked_objects"]:
                            context["skills"][skill]["skill"]["objects_modifier"][lo] = dict()
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
                    if "linked_objects" in self.object_modifier[skill][obj]:
                        for lo in self.object_modifier[skill][obj]["linked_objects"]:
                            context["skills"][skill]["skill"]["objects_modifier"][lo][modifier] = mod_value
            print(context["skills"][skill]["skill"]["objects_modifier"])

    def calculate_cost(self, result: TaskResult) -> QMetric:
        if sum(self.cost_function.optimum_weights.values()) != 1:
            logger.error("Sum of cost_function.optimum_weights must be 1.")
            raise CostFunctionError

        cost_per_weight = dict.fromkeys(cost_types, 0)
        for cost_type in cost_per_weight.keys():
            cost_per_weight[cost_type] += result.q_metric.cost[cost_type]

        cost = 0

        for cost_type in cost_per_weight.keys():
            if self.cost_function.optimum_weights[cost_type] > 0:
                var = cost_per_weight[cost_type]
                cost += self.cost_function.optimum_weights[cost_type] * (
                        eval(self.cost_function.optimum_expressions[cost_type]) / self.cost_function.max_cost[
                    cost_type]) * self.cost_function.normal_cost

                if eval(self.cost_function.optimum_expressions[cost_type]) > self.cost_function.max_cost[cost_type]:
                    logger.debug("Exceeded maximum cost! Cost is " + str(
                        eval(self.cost_function.optimum_expressions[cost_type])) + ", maximum cost is " + str(
                        self.cost_function.max_cost[cost_type]))
                    result.q_metric.success = False

        heuristic = 0
        var = result.q_metric.heuristic
        heuristic += eval(self.cost_function.heuristic_expressions)

        if result.q_metric.success is True:
            result.q_metric.final_cost = cost
            result.q_metric.optimal = cost < self.optimum_thr
        else:
            result.q_metric.final_cost = heuristic + self.cost_function.normal_cost

        return result.q_metric
