import copy
from typing import Tuple
import numpy as np


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

        if "init_knowledge" in data_tmp["meta"] and data_tmp["meta"]["init_knowledge"]["content"]:
            self.knowledge = data_tmp["meta"]["init_knowledge"]["content"]["parameters"]
        else:
            self.knowledge = None
        self.uuid = data_tmp["meta"]["uuid"]
        self.tags = data_tmp["meta"]["tags"]

    def get_cost_per_trial(self, episode_length: int = 1) -> list:
        cost_raw = []
        cost = []
        if len(self.trials) % episode_length != 0:
            print("Number of trials and episode length do not fit.")
            return []
        n_episodes = len(self.trials) / episode_length
        for t in self.trials:
            cost_raw.append(t["cost"])
        for i in range(int(n_episodes)):
            cost.append(np.min(np.asarray(cost_raw[i * episode_length : i * episode_length + episode_length])))

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

    def get_lowest_cost(self):
        costs = self.get_cost_per_trial()
        return min(costs)

    def get_best_theta(self):
        best_theta = self.trials[0]["theta"]
        best_cost = self.trials[0]["cost"]
        for t in self.trials:
            if t["cost"] < best_cost:
                best_cost = t["cost"]
                best_theta = t["theta"]
        return best_theta

    def get_best_theta_norm(self):
        best_theta = self.get_best_theta()
        best_theta_norm = {}
        for param in best_theta.keys():
            min_param = self.meta_data["domain"]["limits"][param][0]
            max_param = self.meta_data["domain"]["limits"][param][1]
            best_theta_norm[param] = normalize(best_theta[param], min_param, max_param)
        return best_theta_norm
    
    def get_knowledge_norm(self):
        if self.knowledge is None:
            return None
        knowledge_norm = {}
        for param in self.knowledge.keys():
            min_param = self.meta_data["domain"]["limits"][param][0]
            max_param = self.meta_data["domain"]["limits"][param][1]
            knowledge_norm[param] = normalize(self.knowledge[param], min_param, max_param)
        return knowledge_norm
    
    def get_default_centroid(self):
        return self.meta_data["domain"]["x_0"]
    
    def normalize_result(self, data_dict):
        for param in data_dict.keys():
            min_param = self.meta_data["domain"]["limits"][param][0]
            max_param = self.meta_data["domain"]["limits"][param][1]
            data_dict[param] = normalize(data_dict[param], min_param, max_param)
        return data_dict

class Knowledge:
    def __init__(self, data: dict):
        data_tmp = copy.deepcopy(data)
        del data_tmp["_id"]
        self.meta_data = data_tmp["meta"]
        self.sources = data_tmp["meta"]["knowledge_source"]
        self.parameter_dict = data_tmp["parameters"]
        self.expected_cost = data_tmp["meta"]["expected_cost"]
        self.confidence = data_tmp["meta"]["confidence"]
    
    def get_theta(self):
        parameter_list = []
        for key in self.parameter_dict.keys():
            parameter_list.append(self.parameter_dict[key])
        return parameter_list
        
def normalize(d, min, max):
    return (d - min) / (max - min)

def denormalize(d_norm, min, max):
    return d_norm * (max - min) + min
