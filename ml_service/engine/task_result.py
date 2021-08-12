import logging


logger = logging.getLogger("ml_service")


cost_types = ["time", "contact_forces", "effort_avg", "effort_total", "distance", "custom"]


class QMetric:
    def __init__(self):
        self.final_cost = None
        self.success = None
        self.cost = dict()
        self.heuristic = None
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
        self.n_variations = 1
        self.var_failures = 0

    def add_variation(self, q_metric: QMetric):
        self.n_variations += 1
        if q_metric.success is False and self.q_metric.success is True:
            self.q_metric.final_cost = q_metric.final_cost
        elif q_metric.success is True and self.q_metric.success is False:
            pass
        else:
            self.q_metric.final_cost = (self.q_metric.final_cost * self.n_variations + q_metric.final_cost) / self.n_variations

        if q_metric.success is False:
            self.var_failures += 1
            self.q_metric.success = False

        self.q_metric.heuristic = (self.q_metric.heuristic * self.n_variations * self.var_failures + q_metric.heuristic) / (self.n_variations * self.var_failures)
        for c in self.q_metric.cost:
            self.q_metric.cost[c] = (self.q_metric.cost[c] * self.n_variations + q_metric.cost[c]) / self.n_variations



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
                if r["heuristic"] is not None:
                    self.q_metric.heuristic += r["heuristic"]

        self.q_metric.success = result["success"]
        if self.q_metric.success is False:
            self.var_failures = 1
        self.errors = result["error"]

        return True
