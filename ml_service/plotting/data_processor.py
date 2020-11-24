from plotting.result import Result
import numpy as np
from typing import Tuple


class DataError(Exception):
    pass


class DataProcessor:
    def __init__(self):
        pass

    def find_maximum_length(self, lists: list):
        length = 0
        for l in lists:
            if len(l) > length:
                length = len(l)
        return length

    def get_collection_of_costs(self, results: list, decreasing: bool = False, episode_length: int = 1) -> list:
        costs = []
        for r in results:
            if decreasing is True:
                costs.append(self.get_monotonically_decreasing_cost(r.get_cost_per_trial(episode_length)))
            else:
                costs.append(r.get_cost_per_trial(episode_length))

        n_trials = self.find_maximum_length(costs)

        for c in costs:
            if len(c) < n_trials:
                c.extend([c[-1]] * (n_trials - len(c)))
        return costs

    def get_optima_by_task_identity(self, results: list, percentage: float) -> np.ndarray:
        arr = np.zeros((len(results), 7))
        for i in range(len(results)):
            if len(results[i].trials) < 1:
                continue
            arr[i, 0] = results[i].meta_data["cost_function"]["geometry_factor"]
            arr[i, 1:-1] = results[i].meta_data["cost_function"]["optimum_weights"]
            cost_grid_max = np.asarray(results[i].meta_data["cost_function"]["max_cost"])
            max_cost = cost_grid_max[0] * arr[i, 1] + cost_grid_max[1] * arr[i, 2] + cost_grid_max[2] * arr[i, 3] + \
                       cost_grid_max[3] * arr[i, 4] + cost_grid_max[4] * arr[i, 5]
            cost = self.get_monotonically_decreasing_cost(results[i].get_cost_per_trial())
            max_cost = 1
            arr[i, -1] = (max_cost - cost[-1]) * percentage + cost[-1]
        return arr

    def get_average_cost(self, results: list, decreasing: bool = False, episode_length: int = 1) -> np.ndarray:
        return np.average(np.asarray(self.get_collection_of_costs(results, decreasing, episode_length)), 0)

    def get_monotonically_decreasing_cost(self, cost: np.ndarray) -> np.ndarray:
        cost_monotone = cost
        if len(cost_monotone) == 0:
            raise DataError
        c_0 = cost_monotone[0]
        for i in range(1, len(cost_monotone)):
            if cost[i] > c_0:
                cost_monotone[i] = c_0
            if cost_monotone[i] < c_0:
                c_0 = cost_monotone[i]
        return cost_monotone

    def get_total_times(self, results: list) -> np.ndarray:
        times = []
        for r in results:
            times.append(r.get_total_time())
        return np.asarray(times)

    def get_parameter_over_cost(self, result: Result, parameter: str) -> Tuple[list, list]:
        cost = result.get_cost_per_trial()
        parameters = result.get_theta_per_trial()
        p = []
        for i in range(len(parameters)):
            p.append(parameters[i][parameter])

        cost_sorted = [x for _, x in sorted(zip(p, cost))]
        return cost_sorted, sorted(p)

    def get_agent_results(self, results: list) -> dict:
        agents = []
        ordered_results = {}
        for r in results:
            tags = set(r.meta_data["tags"])
            if tags not in agents:
                agents.append(tags)
                ordered_results[str(tags)] = []
                ordered_results[str(tags)].append(r)
            else:
                ordered_results[str(tags)].append(r)
        return ordered_results

    def get_cumulative_time(self, results: list) -> np.ndarray:
        times_cum = []
        for r in results:
            if len(times_cum) == 0:
                times_cum.append(r.get_total_time())
            else:
                times_cum.append(times_cum[-1] + r.get_total_time())
        return np.asarray(times_cum)

    def get_total_trials(self, results: list) -> np.ndarray:
        trials_per_task = []
        for r in results:
            trials_per_task.append(r.get_total_trials())
        return np.asarray(trials_per_task)

    def sort_over_time(self, results: list) -> list:  # sort over end-time
        return sorted(results, key=lambda r: (r.starting_time + r.total_time))

    def get_average_theta(self):
        pass

    def get_std_cost(self, results: list) -> np.ndarray:
        return np.std(np.asarray(self.get_collection_of_costs(results)), 0)

    def get_std_theta(self):
        pass

    def dict_to_list(self, d: dict) -> list:
        '''returns a list with dict contents'''
        l = []
        for key in d.keys():
            l.append(d[key])
        return l
