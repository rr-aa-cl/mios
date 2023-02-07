import numpy as np
import logging
from plotting.data_acquisition import get_experiment_data
from plotting.data_processor import DataProcessor
import matplotlib.pyplot as plt


logger = logging.getLogger("ml_service")


class Analyzer:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.result = None

    def load_data(self, host: str, task_type: str, uuid: str):
        self.result = get_experiment_data(host, task_type, uuid=uuid)

    def analyze_data(self, host: str, task_type: str, uuid: str):
        self.load_data(host, task_type, uuid)
        self.get_best_theta_variance()

    def get_parameters_over_cost(self):
        parameters = list(self.result.get_parameters())
        fig, axes = plt.subplots(len(parameters))
        p_cnt = 0
        for a in axes:
            cost, param = self.data_processor.get_parameter_over_cost(self.result, parameters[p_cnt])
            a.plot(cost, param)
            min_param = self.result.meta_data["domain"]["limits"][parameters[p_cnt]][0]
            max_param = self.result.meta_data["domain"]["limits"][parameters[p_cnt]][1]
            a.set_ylim(min_param, max_param)
            a.set_xlim(0, 1)
            p_cnt += 1

    def get_best_theta_variance(self):
        theta = self.result.get_theta_per_trial()
        cost = self.result.get_cost_per_trial()
        theta_sorted = [x for _, x in sorted(zip(cost, theta))]

        theta_matrix = np.zeros((len(self.result.get_parameters()),int(len(theta_sorted) / 10)))

        params = list(self.result.get_parameters())
        params.sort()
        for i in range(len(params)):
            for j in range(int(len(theta_sorted) / 20)):
                theta_matrix[i][j] = (theta_sorted[j][params[i]] - self.result.meta_data["domain"]["limits"][params[i]][0]) / \
                                     (self.result.meta_data["domain"]["limits"][params[i]][1] -
                                      self.result.meta_data["domain"]["limits"][params[i]][0])

        centroids = []
        std = []
        for i in range(theta_matrix.shape[0]):
            centroids.append(np.average(theta_matrix[i]))
            std.append(np.std(theta_matrix[i]))

        print(centroids)
        print(std)
