import numpy as np
from copy import deepcopy
import time

from skopt import forest_minimize

from ml_methods.wrappers.learner_base import LearnerBase


class LearnerForest(LearnerBase):
    def __init__(self):
        super(LearnerForest, self).__init__()

        self.constraints_multiplier = []
        self.failure_cost = None
        self.constraints_base_cost = None
        self.base_estimator = None
        self.max_trials = None
        self.n_random_starts = None
        self.acq_func = None
        self.acq_func_points = None
        self.x_init = None
        self.y_init = None
        self.kappa = None
        self.xi = None

        self.bounds = []
        self.bounds_feasibility = []

        self.n_samples = None

    def _init_learner(self):

        self.flag_stop = False

    def _learn_task(self):

        self.mat_bounds = []
        for p in self.domain:
            self.mat_bounds.append(p["bounds"])

        self.mat_bounds = np.array(self.mat_bounds)
        print([(0, 1)] * len(self.domain))

        if self.base_params is not None:
            self.x_init = dict()
            for i in range(len(self.domain)):
                # x_init[i]=(self.domain[i]['bounds'][1]-self.domain[i]['bounds'][0])/2
                for key, val in self.base_params.items():
                    if self.domain[i]['name'] == key:
                        print('%s has value: %s' % (self.domain[i]['name'], val))
                        self.x_init[key] = self._normalize2(val, self.mat_bounds[i, 0], self.mat_bounds[i, 1])
                        print('%s has normal value: %s' % (self.domain[i]['name'], self.x_init[key]))

        if self.x_init is not None:
            print('No prior knowledge available but initial centroid is given.')
            x_init = [0.0] * len(self.domain)
            for i in range(len(self.domain)):
                # x_init[i]=(self.domain[i]['bounds'][1]-self.domain[i]['bounds'][0])/2
                for key, val in self.x_init.items():
                    if self.domain[i]['name'] == key:
                        print('%s has value: %s' % (self.domain[i]['name'], val))
                        x_init[i] = val

            x0 = x_init

        else:
            print('No prior knowledge available and no initial centroid given, reverting to standard.')
            x0 = None

        res = forest_minimize(self._run_trial,
                              [(0.0, 1.0)] * len(self.domain),
                              base_estimator=self.base_estimator,
                              n_calls=self.max_trials,
                              n_random_starts=self.n_random_starts,
                              x0=x0,
                              acq_func=self.acq_func,
                              n_points=self.acq_func_points, xi=self.xi,
                              kappa=self.kappa)

        print(res.x)
        print(res.fun)

    def _run_trial(self, x):
        print(x)
        try:
            if self.flag_stop is True:
                return -1
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

            print("Cost: " + str(cost_final))
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

    def _transform_to_real(self, x):
        x_n = x
        x = self._unnormalize(x)
        for i in range(len(x)):
            if self.domain[i]['name'] == 'gamma_b_t' or self.domain[i]['name'] == 'gamma_b_r' or \
                    self.domain[i]['name'] == 'gamma_a_t' or self.domain[i]['name'] == 'gamma_a_r':
                tmp = self._unnormalize2(1 - x_n[i], np.log10(1 / self.mat_bounds[i, 1]),
                                         np.log10(1 / self.mat_bounds[i, 0]))
                x[i] = 1 / pow(10, tmp)

        return x

    def _read_local_options(self, default_options):

        self.failure_base_cost = self.read_option('failure_base_cost', default_options)
        self.base_estimator = self.read_option('base_estimator', default_options)
        self.acq_func = self.read_option('acq_func', default_options)
        self.acq_func_points = self.read_option('acq_func_points', default_options)
        self.max_trials = self.read_option('max_trials', default_options)
        self.n_random_starts = self.read_option('n_random_starts', default_options)
        self.x_init = self.read_option('x_init', default_options)
        self.xi = self.read_option('xi', default_options)
        self.kappa = self.read_option('kappa', default_options)

        if 'options' not in self.definition:
            print("No learner options for this task, reverting to standard")
            return True

        if 'forest' not in self.definition['options']:
            print("No learner options for this task, reverting to standard")
            return True

        options_overwrite = self.definition["options"]["forest"]

        if 'failure_base_cost' in options_overwrite:
            self.failure_base_cost = options_overwrite['failure_base_cost']
