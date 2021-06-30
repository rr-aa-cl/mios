import logging


logger = logging.getLogger("ml_service")


cost_types = ["time", "contact_forces", "effort_avg", "effort_total", "distance", "custom"]


class QMetric:
    def __init__(self):
        self.final_cost = None
        self.success = None
        self.cost = dict()
        self.heuristic = dict()
        self.optimal = False

    def to_dict(self) -> dict:
        q_metric_dict = {
            "final_cost": self.final_cost,
            "success": self.success,
            "cost": self.cost,
            "heuristic": self.heuristic,
            "optimal": self.optimal,
        }
        return q_metric_dict


class TaskResult:
    def __init__(self):

        self.errors = []
        self.q_metric = QMetric()

    def calculate(self, result: dict) -> bool:
        if "success" not in result:
            logger.error("No success indicator in result.")
            return False

        if "skill_results" not in result or result["skill_results"] is None:
            logger.error("No skill results in result.")
            return False

        self.q_metric.cost = dict.fromkeys(cost_types, 0)
        self.q_metric.heuristic = 0
        for skill, r in result["skill_results"].items():
            for cost_type, cost_value in r["cost"].items():
                self.q_metric.cost[cost_type] += r["cost"][cost_type]
                self.q_metric.heuristic += r["heuristic"]

        self.q_metric.success = result["success"]
        self.errors = result["error"]

        return True
