from plotting.result import Result
import numpy as np


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

    def get_collection_of_costs(self, results: list) -> list:
        costs = []
        for r in results:
            costs.append(r.get_cost_per_trial())

        n_trials = self.find_maximum_length(costs)

        for c in costs:
            if len(c) < n_trials:
                c.extend([c[-1]] * (n_trials - len(c)))
        return costs

    def get_average_cost(self, results: list) -> np.ndarray:
        return np.average(np.asarray(self.get_collection_of_costs(results)), 0)

    def get_monotonically_decreasing_cost(self, cost: np.ndarray):
        cost_monotone = cost
        if len(cost_monotone) == 0:
            raise DataError
        c_0 = cost_monotone[0]
        for i in range(1,len(cost_monotone)):
            if cost[i] > c_0:
                cost_monotone[i] = c_0
            if cost_monotone[i] < c_0:
                c_0 = cost_monotone[i]
        return cost

    def get_average_theta(self):
        pass

    def get_std_cost(self, results: list) -> np.ndarray:
        return np.std(np.asarray(self.get_collection_of_costs(results)), 0)

    def get_std_theta(self):
        pass
