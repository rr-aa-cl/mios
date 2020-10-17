import copy
from typing import Tuple


class Result:
    def __init__(self, data: dict):
        data_tmp = copy.deepcopy(data)
        del data_tmp["_id"]
        n_trials = len(data_tmp) - 2
        self.trials = []
        for i in range(n_trials):
            self.trials.append(data_tmp["n" + str(i+1)])
        self.meta_data = data_tmp["meta"]
        if data_tmp.get("final_results",False):
            self.total_time = data_tmp["final_results"]["time"]
            self.total_trials = data_tmp["final_results"]["n_trials"]
        else: 
            self.total_trials = 0
            self.total_time = 0
        self.starting_time = data_tmp["meta"]["t_0"]

    def get_cost_per_trial(self) -> list:
        cost = []
        for t in self.trials:
            cost.append(t["cost"])
        return cost

    def get_parameters(self) -> set:
        theta = self.trials[0]["theta"]
        parameters = set()
        for key, val in theta.items():
            parameters.add(key)

        return parameters

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

    def get_total_time(self) -> float:
        return self.total_time
    
    def get_total_trials(self) -> int:
        return self.total_trials
