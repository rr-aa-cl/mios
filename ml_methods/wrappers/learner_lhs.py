import numpy as np
from copy import deepcopy
import time

from pyDOE import *

from ml_methods.wrappers.learner_base import LearnerBase


class LearnerLHS(LearnerBase):
    def __init__(self):
        super(LearnerLHS, self).__init__()

        self.constraints_multiplier = []
        self.failure_cost = None
        self.constraints_base_cost = None

        self.bounds = []
        self.bounds_feasibility = []

        self.n_samples = None

    def _init_learner(self):

        self.flag_stop = False

    def _learn_task(self):

        grid=lhs(len(self.domain),samples = self.n_samples)
        cost = np.zeros((self.n_samples,1))
        success = np.zeros((self.n_samples,1))
        constraints = np.zeros((self.n_samples,10))
        #p = Pool(self.n_samples)
        cost_success = list()
        #self._run_trial(grid)

        #p.map(self._run_trial,grid)
        self.mat_bounds = []
        for p in self.domain:
            self.mat_bounds.append(p["bounds"])

        self.mat_bounds = np.array(self.mat_bounds)

        for i in range(0,grid.shape[0]):
            if self.flag_stop is True:
                break
            self._run_trial(grid[i])

    def _run_trial(self, x):
        try:
            print('Starting trial ' + str(self.n_trial) + '...')
            for i in range(len(x)):
                if x[i] < self.domain[i]['bounds'][0]:
                    x[i] = self.domain[i]['bounds'][0]
                if x[i] > self.domain[i]['bounds'][1]:
                    x[i] = self.domain[i]['bounds'][1]

            x = self._transform_to_real(x)
            params = deepcopy(self.param_template)
            #            params['skills'] = self.config['skills']
            # print(params)

            for i in range(len(x)):
                param_keys = str.split(str(self.domain[i]['name']), ".")
                param_keys[len(param_keys) - 1] = str.split(str(param_keys[len(param_keys) - 1]), '-')[0]
                self._set_param(x[i], i, params)

            param_log = deepcopy(params)

            job = dict()
            job["params"] = params
            job["param_log"] = param_log
            job["id"] = 0
            job["params_pure"] = x
            job["n_trial"] = self.n_trial
            self.lb.job_queue.put(deepcopy(job))
            self.n_trial += 1

            cost_final = -1
            while self.lb.job_completed.empty():
                time.sleep(0.1)
            while not self.lb.job_completed.empty():
                done_job = self.lb.job_completed.get()

                response = done_job["response"]
                success = response["success"]
                cost_suc = response["cost_suc"]
                cost_err = response["cost_err"]
                nominal = response["nominal_termination"]

                if success == False:
                    cost_final = self.failure_base_cost + np.exp(cost_err * 100) - 1
                else:
                    cost_final = cost_suc

                if np.isnan(cost_final) or np.isinf(cost_final) or cost_final < 0:
                    cost_final = self.failure_base_cost + np.exp(0.1 * 100)

                self._write_meta_data(done_job["n_trial"], done_job["param_log"], cost_final, success,
                                      done_job["t_finish"])

                # params[done_job["id"]]= done_job["params_pure"]
                self.lb.job_completed.task_done()

            print("Done.")
            return cost_final
        except TypeError:
            return len(x) * [(0)]

    def _setup_exp(self):
        for i in range(len(self.rpc_url)):
            self.lb.rpc_call(self.rpc_url[i], "setupExp", self.skill_params_default)

    def _terminate_exp(self):
        for i in range(len(self.rpc_url)):
            self.lb.rpc_call(self.rpc_url[i], "terminateExp", self.skill_params_default)

    def _normalize(self, x):
        return (x - self.mat_bounds[:, 0]) / (self.mat_bounds[:, 1] - self.mat_bounds[:, 0])

    def _normalize2(self, x, min_, max_):
        return (x - min_) / (max_ - min_)

    def _unnormalize(self, x):
        return x * (self.mat_bounds[:, 1] - self.mat_bounds[:, 0]) + self.mat_bounds[:, 0]

    def _unnormalize2(self, x, min_, max_):
        return x * (max_ - min_) + min_

    def _transform_to_real(self,x):
        x_n = x
        x = self._unnormalize(x)
        for i in range(len(x)):
            if self.domain[i]['name'] == 'gamma_b_t' or self.domain[i]['name'] == 'gamma_b_r' or \
                    self.domain[i]['name'] == 'gamma_a_t' or self.domain[i]['name'] == 'gamma_a_r':
                tmp = self._unnormalize2(1 - x_n[i], np.log10(1 / self.mat_bounds[i, 1]),
                                         np.log10(1 / self.mat_bounds[i, 0]))
                x[i] = 1 / pow(10, tmp)

        return x

    def _read_local_options(self):
        options = self.m_db["methods"].find_one({"method": "lhs"})
        self.n_samples = self.read_option('n_samples', options)
        self.failure_base_cost = self.read_option('failure_base_cost', options)

        if 'options' not in self.config:
            print("No learner options for this task, reverting to standard")
            return

        if 'lhs' not in self.config['options']:
            print("No learner options for this task, reverting to standard")
            return

        options_overwrite = self.config["options"]["lhs"]

        if 'n_samples' in options_overwrite:
            self.n_samples = options_overwrite['n_samples']


        if 'failure_base_cost' in options_overwrite:
            self.failure_base_cost = options_overwrite['failure_base_cost']
