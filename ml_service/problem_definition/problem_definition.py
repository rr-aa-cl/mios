from problem_definition.domain import Domain
from engine.task_result import TaskResult
from utils.exception import CostFunctionError
import logging


logger = logging.getLogger("ml_service")


class CostFunction:
    def __init__(self):
        self.optimum_skills = []
        self.optimum_weights = []
        self.optimum_expressions = []
        self.heuristic_skills = []
        self.heuristic_weights = []
        self.heuristic_expressions = []

    def to_dict(self):
        c = {
            "optimum_skills": self.optimum_skills,
            "optimum_weights": self.optimum_weights,
            "optimum_expressions": self.optimum_expressions,
            "heuristic_skills": self.heuristic_skills,
            "heuristic_weights": self.heuristic_weights,
            "heuristic_expressions": self.heuristic_expressions
        }
        return c

    @staticmethod
    def from_dict(cf_dict: dict):
        c = CostFunction()
        c.optimum_skills = cf_dict["optimum_skills"]
        c.optimum_weights = cf_dict["optimum_weights"]
        c.optimum_expressions = cf_dict["optimum_expressions"]
        c.heuristic_skills = cf_dict["heuristic_skills"]
        c.heuristic_weights = cf_dict["heuristic_weights"]
        c.heuristic_expressions = cf_dict["heuristic_expressions"]
        return c


class ProblemDefinition:
    def __init__(self, task_type: str, domain: Domain, default_context: dict, setup_instructions: list, termination_instruction: list,
                 reset_instruction: list, cost_function: CostFunction, tags=None):
        if tags is None:
            tags = []
        self.domain = domain
        self.default_context = default_context
        self.setup_instructions = setup_instructions
        self.termination_instructions = termination_instruction
        self.reset_instructions = reset_instruction
        self.uuid = "INVALID"
        self.task_type = task_type
        self.cost_function = cost_function
        self.tags = tags

    def to_dict(self) -> dict:
        problem_definition = {
            "domain": self.domain.to_dict(),
            "default_context": self.default_context,
            "setup_instructions": self.setup_instructions,
            "termination_instructions": self.termination_instructions,
            "reset_instructions": self.reset_instructions,
            "uuid": self.uuid,
            "task_type": self.task_type,
            "tags": self.tags,
            "cost_function": self.cost_function.to_dict()
        }
        return problem_definition

    @staticmethod
    def from_dict(pd_dict):
        pd = ProblemDefinition(pd_dict["task_type"], Domain.from_dict(pd_dict["domain"]), pd_dict["default_context"],
                               pd_dict["setup_instructions"], pd_dict["termination_instructions"],
                               pd_dict["reset_instructions"], CostFunction.from_dict(pd_dict["cost_function"]),
                               pd_dict["tags"])
        pd.domain = pd_dict["domain"]
        pd.cost_function = pd_dict["cost_function"]

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

    def calculate_cost(self, result: TaskResult) -> float:
        if len(self.cost_function.optimum_expressions) != 3 or len(self.cost_function.optimum_weights) != 3:
            raise CostFunctionError

        if len(self.cost_function.heuristic_expressions) != 3 or len(self.cost_function.heuristic_weights) != 3:
            raise CostFunctionError

        cost_per_weight = [0, 0, 0]
        for s in self.cost_function.optimum_skills:
            cost_per_weight[0] += result.cost[s]["time"]
            cost_per_weight[1] += result.cost[s]["contact_forces"]
            cost_per_weight[2] += result.cost[s]["custom"]

        cost = 0
        for i in range(3):
            var = cost_per_weight[i]
            cost += self.cost_function.optimum_weights[i] * eval(self.cost_function.optimum_expressions[i])

        heuristic_per_weight = [0, 0, 0]
        for s in self.cost_function.heuristic_skills:
            heuristic_per_weight[0] += result.heuristic[s]

        heuristic = 0
        for i in range(3):
            var = heuristic_per_weight[i]
            heuristic += self.cost_function.heuristic_weights[i] * eval(self.cost_function.heuristic_expressions[i])

        return cost + heuristic
