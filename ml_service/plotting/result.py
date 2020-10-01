import copy
from typing import Tuple


class Result:
    def __init__(self, data: dict):
        data_tmp = copy.deepcopy(data)
        del data_tmp["_id"]
        n_trials = len(data_tmp) - 1
        self.trials = []
        for i in range(n_trials):
            self.trials.append(data_tmp["n" + str(i+1)])
        self.meta_data = data_tmp["meta"]

    def get_cost_per_trial(self) -> list:
        cost = []
        for t in self.trials:
            cost.append(t["cost"])
        return cost

    def get_cost_per_time(self) -> Tuple[list, list]:
        cost = []
        time = []
        t_0 = self.trials[0]["t_0"]
        for t in self.trials:
            cost.append(t["cost"])
            time.append(t["t_1"] - t_0)
        return cost, time

    def get_theta_per_trial(self):
        theta = []
        for t in self.trials:
            theta.append(t["theta"])
        return theta

    def get_theta_per_time(self) -> Tuple[list, list]:
        theta = []
        time = []
        t_0 = self.trials[0]["t_0"]
        for t in self.trials:
            theta.append(t["theta"])
            time.append(t["t_1"] - t_0)
        return theta, time
