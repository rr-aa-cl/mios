import logging


logger = logging.getLogger("ml_service")


cost_types = ["time", "contact_forces", "effort_avg", "effort_total", "distance", "desired_force", "desired_pose",
              "custom"]


class QMetric:
    def __init__(self):
        self.final_cost = float("inf")
        self.success = False
        self.cost = dict()
        self.heuristic = float("inf")
        self.optimal = False
        self.success_rate = 0

    def to_dict(self) -> dict:
        q_metric_dict = {
            "final_cost": self.final_cost,
            "success": self.success,
            "cost": self.cost,
            "heuristic": self.heuristic,
            "optimal": self.optimal,
            "success_rate": self.success_rate
        }
        return q_metric_dict


class TaskResult:
    def __init__(self):
        self.errors = []
        self.q_metric = QMetric()
        self.n_variations = 1
    
    def to_dict(self):
        task_result_dict = {
            "q_metric":self.q_metric.to_dict(),
            "n_varialtions": self.n_variations,
            "errors": self.errors
        }
        return task_result_dict

    def add_variation(self, q_metric: QMetric):
        '''
        combine q_metrics: 
        - set success according to worst q_metric in all variations
        - calculate success_rate, cost and heuristic as mean of all variations
        - if success of all q_metric is equal: calculate final_cost as mean of all variations
        '''
        self.n_variations += 1
        if q_metric.success is False and self.q_metric.success is True:
            self.q_metric.final_cost = q_metric.final_cost
        elif q_metric.success is True and self.q_metric.success is False:
            pass
        else:
            self.q_metric.final_cost = (self.q_metric.final_cost * (self.n_variations - 1) + q_metric.final_cost) / self.n_variations

        self.q_metric.success_rate = (self.q_metric.success_rate * (self.n_variations - 1) + int(q_metric.success)) / self.n_variations
        if q_metric.success is False:
            self.q_metric.success = False



        self.q_metric.heuristic = (self.q_metric.heuristic * (self.n_variations - 1) + q_metric.heuristic) / self.n_variations
        for c in self.q_metric.cost:
            self.q_metric.cost[c] = (self.q_metric.cost[c] * (self.n_variations - 1) + q_metric.cost[c]) / self.n_variations

    def calculate(self, result: dict) -> bool:
        '''
        calculate q_metric from mios task result
        input: result (dict) is the feedback json comming from mios
        '''
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
                if r["cost"][cost_type] is None:
                    return False
                self.q_metric.cost[cost_type] += r["cost"][cost_type]
                if r["heuristic"] is not None:
                    self.q_metric.heuristic += r["heuristic"]

        self.q_metric.success = result["success"]
        self.q_metric.success_rate = int(self.q_metric.success)
        self.errors = result["error"]

        return True
