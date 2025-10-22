from definitions.definitions_base import *


class TimeMetric(CostFunctionFactory):
    def __init__(self, skill_class: str, max_cost: float):
        super().__init__(skill_class, {"time": 1}, max_cost, "np.exp(var)")


class ContactForcesMetric(CostFunctionFactory):
    def __init__(self, skill_class: str, max_cost: dict):
        super().__init__(skill_class, {"contact_forces": 1}, max_cost, "np.exp(var)")