import logging


logger = logging.getLogger("ml_service")


class TaskResult:
    def __init__(self):
        self.final_cost = None
        self.cost = dict()
        self.heuristic = dict()
        self.success = None
        self.errors = []

    def calculate(self, result: dict) -> bool:
        if "success" not in result:
            logger.error("No success indicator in result.")
            return False

        if "skill_results" not in result or result["skill_results"] is None:
            logger.error("No skill results in result.")
            return False

        for skill, r in result["skill_results"].items():
            self.cost[skill] = r["cost"]
            self.heuristic[skill] = r["heuristic"]

        self.success = result["success"]
        self.errors = result["error"]

        return True