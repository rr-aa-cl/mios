from problem_definition.domain import Domain
from engine.task_result import TaskResult
import logging


logger = logging.getLogger("ml_service")


class ProblemDefinition:
    def __init__(self, task_type: str, domain: Domain, default_context: dict, setup_instructions: list, termination_instruction: list,
                 reset_instruction: list, cost_function, tags=None):
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
            "uuid": self.uuid,
            "task_type": self.task_type,
            "tags": self.tags
        }
        return problem_definition

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
        return self.cost_function(result.cost, result.heuristic, result.success)