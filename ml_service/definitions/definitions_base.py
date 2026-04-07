from problem_definition.domain import Domain
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.problem_definition import CostFunction
from services.base_service import ServiceConfiguration
import abc
from abc import ABC
from pathlib import Path
import json


class LearnerFactory(ABC):
    def __init__(self, configuration: ServiceConfiguration):
        self.configuration = configuration

    def get_configuration(self):
        return self.configuration


class CostFunctionFactory(ABC):
    def __init__(self, skill_class: str, weights: dict, max_cost: dict, heuristic: str):
        self.cost_function = CostFunction()
        self.cost_function.optimum_skills = [skill_class]
        self.cost_function.heuristic_skills = [skill_class]
        self.cost_function.optimum_weights.update(weights)
        self.cost_function.max_cost.update(max_cost)
        self.cost_function.heuristic_expressions = heuristic

    def get_cost_function(self):
        return self.cost_function


class ProblemDefinitionFactory(ABC):

    def __init__(self, robots: list, skill_class: str, learn_skills: list, setup_skills: list, reset_skills: list, rescue_skils: list,
                 termination_skills: list, cost_function: CostFunctionFactory, objects: dict, mios_port=12000, context_dir: str = None):
        if context_dir is None:
            # Default to a path relative to this file
            self.context_dir = Path(__file__).parent.parent.parent / "python" / "taxonomy" / "default_contexts"
        else:
            self.context_dir = Path(context_dir)

        self.skill_class = skill_class
        self.cost_function = cost_function
        self.robots = robots
        self.objects = objects
        self.mios_port = mios_port

        self.learn_context = dict()
        self.setup_instructions = list()
        self.reset_instructions = list()
        self.rescue_instructions = list()
        self.termination_instructions = list()

        self.load_default_skill_contexts(learn_skills, setup_skills, reset_skills, rescue_skils, termination_skills)
        self.modify_contexts()
        #self.run_setup()

        self.limits = self.get_limits()
        self.mapping = self.get_mapping()
        self.x_0 = self.get_initial_values()
        self.ground_skills(self.objects)
        self.domain = Domain(self.limits, self.mapping, self.x_0)

    def get_problem_definition(self, task_name: str, identity: list = None) -> ProblemDefinition:
        if identity is None:
            identity = [1]
        pd = ProblemDefinition(self.skill_class, task_name, self.domain, self.learn_context,
                               self.setup_instructions, self.termination_instructions, self.reset_instructions, self.rescue_instructions,
                               self.cost_function.get_cost_function(), identity, tags=[self.skill_class, task_name])
        return pd

    @abc.abstractmethod
    def get_limits(self) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def get_mapping(self) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def get_initial_values(self) -> dict:
        raise NotImplementedError

    def _load_skill_info(self, skills: list) -> dict:
        """Helper to load skill JSON files and wrap with common parameters (Phase 5)."""
        context = {
            "name": "GenericTask",
            "parameters": {"skill_types": [], "skill_names": []},
            "skills": {}
        }
        for s_type, s_name, s_file in skills:
            file_path = self.context_dir / f"{s_file}.json"
            try:
                with open(file_path, "r") as f:
                    skill_data = json.load(f)
                    context["skills"][s_name] = skill_data
                    context["parameters"]["skill_types"].append(s_type)
                    context["parameters"]["skill_names"].append(s_name)
                    # Add common nullspace control
                    context["skills"][s_name]["control"]["nullspace"] = {
                        "K_theta": [20, 20, 15, 10, 7, 5, 2],
                        "xi_theta": [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
                        "active": True
                    }
            except FileNotFoundError:
                print(f"Warning: Skill file {file_path} not found.")
        return context

    def load_default_skill_contexts(self, learn_skills: list, setup_skills: list, reset_skills: list, rescue_skills: list,
                                    termination_skills: list):
        """Unified loader for all skill contexts (Phase 5)."""
        self.learn_context = self._load_skill_info(learn_skills)
        
        setup_ctx = self._load_skill_info(setup_skills)
        self.setup_instructions.append({"method": "start_task", "parameters": setup_ctx})
        
        reset_ctx = self._load_skill_info(reset_skills)
        self.reset_instructions.append({"method": "start_task", "parameters": reset_ctx})
        
        rescue_ctx = self._load_skill_info(rescue_skills)
        self.rescue_instructions.append({"method": "start_task", "parameters": rescue_ctx})
        
        term_ctx = self._load_skill_info(termination_skills)
        self.termination_instructions.append({"method": "start_task", "parameters": term_ctx})

    def modify_contexts(self):
        pass

    def run_setup(self):
        pass

    @abc.abstractmethod
    def ground_skills(self, objects: dict):
        raise NotImplementedError
