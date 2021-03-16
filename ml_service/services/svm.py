import logging
import numpy as np
import random
import deap
import time

from sklearn.svm import SVC
from sklearn import mixture

from deap import creator

from pyDOE import lhs

from engine.engine import Trial
from services.base_service import BaseService
from services.base_service import ServiceConfiguration

from xmlrpc.client import ServerProxy

logger = logging.getLogger("ml_service")


class SVMConfiguration(ServiceConfiguration):
    def __init__(self):
        super().__init__("svm")
        self.failure_base_cost = -1
        self.target_cost = None
        self.n_trials = 400
        self.batch_width = 1  # retrain after every trial
        self.n_immigrant = 0

    def __del__(self):
        print("DESTRUCTOR")

    def _to_dict(self):
        config = {
            "failure_base_cost": self.failure_base_cost,
            "n_trials": self.n_trials,
            "target_cost": self.target_cost,
            "batch_width": self.batch_width,
            "n_immigrant": self.n_immigrant
        }
        return config

    def _from_dict(self, config_dict):
        self.failure_base_cost = config_dict["failure_base_cost"]
        self.n_trials = config_dict["n_trials"]
        self.target_cost = config_dict["target_cost"]
        self.batch_width = config_dict["batch_width"]
        self.n_immigrant = config_dict["n_immigrant"]


class SVMService(BaseService):
    def __init__(self):
        super(SVMService, self).__init__()

        self.constraints_multiplier = []
        self.failure_cost = None
        self.maxReward = 0

        self.bounds = []
        self.bounds_feasibility = []

        self.sampleCounter = 0
        self.cnt_trial = 0
        self.cnt_batch = 0
        self.globalcost = []
        self.gmm_samples = []
        self.bestSample = []
        self.svmCounter = 0
        self.minCost = np.infty
        self.success = []
        self.rewards = []
        self.svm_samples = []
        self.classifierActive = False
        self.gmm_active = False
        self.mean = 0
        self.episodes = 0
        self.numberOfParameters = 0
        self.target_cost = None

    def _initialize(self):

        self.episodes = self.configuration.n_trials / self.configuration.batch_width
        self.numberOfParameters = 2

        self.limits = self.problem_definition.domain.limits

        self.engine.register_stop_condition(self._is_learned)

    @property
    def _learn_task(self):
        self.mat_bounds = []
        self.numberOfParameters = len(self.limits)
        for p in self.limits.keys():
            self.mat_bounds.append(self.limits[p])

        self.mat_bounds = np.array(self.mat_bounds)
        self.bounds = self.mat_bounds
        self.cnt_batch = 0
        # if self.adapt_to_agents is True:
        #     self.configuration.n_trials = len(self.hosts)

        for i in range(0, int(self.configuration.n_trials / self.configuration.batch_width)):
            if self.keep_running is False:
                break
            self._setSamples(self.cnt_batch)
            self._run_trial_par(self.action_list_norm)
            self._trainSVM()

        self.problem_data = {
            "parameters": self.bestSample,
            "cost": self.minCost,
            "success": True
        }

        self.stop()

        if self.target_cost is not None:
            if self.minCost > self.target_cost:
                print('Target cost not reached')
                return False
            else:
                print('Target cost reached')
                return True
        else:
            return True

    def _run_trial_par(self, x_set: list):
        """ create array of rpc params for input """
        self.cnt_trial = 0
        print("Evaluating batch " + str(self.cnt_batch))
        self.cnt_batch += 1

        self.cnt_trial += 1

        trial_uuids = dict()

        if self.knowledge_source is None:
            kb = None
        else:
            kb = ServerProxy("http://" + self.knowledge_source["kb_location"] + ":8001")

        x_set_external = x_set[len(x_set) - self.configuration.n_immigrant:]
        x_set = x_set[:len(x_set) - self.configuration.n_immigrant]
        print(len(x_set) + len(x_set_external))

        for x in x_set:
            uuid = self.push_trial(x)
            trial_uuids[uuid] = x

        costs = []
        self.success_ratio = 0
        for uuid in trial_uuids:
            result = self.wait_for_result(uuid)
            if result.final_cost is None:
                logger.error("None was returned as cost, invoking stop.")
                self.stop()
                costs.append((0,))
            else:
                self.success_ratio += result.success
                costs.append((result.final_cost,))
            if kb is not None:
                theta = []
                for i in range(len(trial_uuids[uuid])):
                    theta.append(float(trial_uuids[uuid][i]))
                kb.push_trial(self.host_name, theta, float(result.final_cost), self.configuration.batch_width)
                # kb.push_trial_2(theta, float(result.final_cost), self.problem_definition.cost_function.geometry_factor)

        self.success_ratio /= float(len(trial_uuids))

        if kb is not None:
            while True:
                new_set = kb.request_trials(self.configuration.n_immigrant)
                # x_set_external_tmp = []
                # for i in range(len(x_set_external)):
                #     x_set_external_tmp.append([])
                #     for j in range(len(x_set_external[i])):
                #         x_set_external_tmp[i].append(float(x_set_external[i][j]))
                # cost_external = kb.request_online_evaluation(x_set_external_tmp, self.problem_definition.cost_function.geometry_factor)
                if new_set is False:
                    print("Not enought yet")
                    time.sleep(1)
                    continue
                else:
                    break
            for i in new_set:
                x_set.append(i[0])
                costs.append((i[1],))
            # for i in range(len(x_set_external)):
            #     x_set.append(x_set_external[i])
            #     costs.append((cost_external[i],))

        costs_tmp = []
        for c in costs:
            costs_tmp.append(c[0])

        for i in range(0, len(costs)):
            if costs_tmp[i] <= 0:
                continue
            reward = 1 / costs_tmp[i]
            if costs_tmp[i] < self.minCost:
                self.minCost = costs_tmp[i]
                self.bestSample = x_set[i]
            if costs_tmp[i] == self.configuration.failure_base_cost or costs_tmp[i] == 1000000000:
                reward = 0

            _class = 0
            if reward > self.mean:
                _class = 1
                self.svmCounter += 1

            self.svm_samples.append(x_set[i])
            self.success.append(_class)
            self.rewards.append(reward)
            if self.maxReward < reward:
                self.maxReward = reward
                self.bestSample = x_set[i]
        logger.debug("SVM costs: " + str(costs))
        return costs

    def _run_trial(self, x):
        print('RUN_TRIAL')
        pass

    def _param2norm(self, x, i):
        r = (x - self.bounds[i][0]) / (self.bounds[i][1] - self.bounds[i][0])
        return r

    def _norm2param(self, x, i):
        r = self.bounds[i][0] + \
            (self.bounds[i][1] - self.bounds[i][0]) * x
        return r

    def _unnormalize2(self, x, min_, max_):
        return x * (max_ - min_) + min_

    def _norms2params(self, x):
        params = np.zeros(self.numberOfParameters)
        for i in range(0, self.numberOfParameters):
            params[i] = self._norm2param(x[i], i)
        return params

    def _params2norms(self, x):
        norms = np.zeros(self.numberOfParameters)
        for i in range(0, self.numberOfParameters):
            norms[i] = float(self._param2norm(x[i], i))
        return norms

    def _setSamples(self, index):
        self.action_list_norm = []

        i = 0
        counter = 0
        if index == 0:  # when first run use knowledge if available
            if self.centroid is not None:
                self.action_list_norm.append([float(param) for param in self.centroid])
            else:
                temp_param_norm_samples = lhs(self.numberOfParameters, samples=self.configuration.batch_width)
                for t in temp_param_norm_samples:
                    self.action_list_norm.append(t)
        else:
            while i < self.configuration.batch_width:
                if counter >= 1000:
                    action_norm = np.random.uniform(0, 1, self.numberOfParameters)
                    if self.gmm_active is True:
                        action_norm = self.getGmmSample()

                    self.action_list_norm.append(action_norm)
                    i += 1
                    counter = 0
                    # print "added innovation"
                    continue

                if self.classifierActive is True:
                    if self.gmm_active is True:
                        action_norm = self.getGmmSample()
                    else:
                        action_norm = np.random.uniform(0.0, 1.0, self.numberOfParameters)

                    j = 0
                    # print action_norm
                    for a in action_norm:
                        if a < 0:
                            action_norm[j] = 0
                        if a > 1:
                            action_norm[j] = 1
                        j += 1
                    aa = action_norm
                    aa = aa.reshape([1, -1])
                    prediction = self.classifier.predict(aa)
                    # print prediction

                    if prediction == 1:
                        # raw_input("es passiert was!")
                        self.action_list_norm.append(action_norm)
                        i += 1

                    else:
                        # print " rejected"
                        counter += 1
                        continue
                else:
                    action_norm = np.random.uniform(0.0, 1.0, self.numberOfParameters)
                    action = self._norms2params(action_norm)

                    self.action_list_norm.append(action_norm)
                    i += 1

    def getGmmSample(self):
        lm = len(self.sampling_gmm.means_)
        if self.sampleCounter >= lm:
            self.sampleCounter = lm - 1

        x = np.random.multivariate_normal(self.sampling_gmm.means_[self.sampleCounter],
                                          np.diag(self.sampling_gmm.covariances_[self.sampleCounter]))

        self.sampleCounter += 1

        return x

    def _trainSVM(self):
        if self.svmCounter >= 5:
            self._preprocessSamples()
            self.mean = self._calculateMeanReward()
            self._redefineSamples()
            # raw_input (self.mean)

            # self.classifier.fit(self.svm_samples,self.success)

            tt = 0
            self.td = 0

            gammas = [1000]

            for i in gammas:
                d = i

                clf = SVC(C=100000)
                clf.fit(self.svm_samples, self.success)
                temp = np.abs(clf.decision_function(self.svm_samples))
                # print(clf.decision_function(self.svm_samples))

                if tt < temp.min():
                    self.td = d
                    tt = temp.min()
                    self.classifier = clf

            # self._plotData()

            self.classifierActive = True

            if self.svmCounter >= 15 and len(self.gmm_samples) > 2:

                for x in self.classifier.support_vectors_:
                    pass
                    # self.gmm_samples.append(x)

                lowest_bic = np.infty
                bic = []
                maxcomponents = 8
                if maxcomponents > len(self.gmm_samples):
                    maxcomponents = len(self.gmm_samples)
                maxcomponents = 1
                for i in range(0, maxcomponents):
                    gmm = mixture.GaussianMixture(n_components=i + 1, covariance_type='diag')
                    # raw_input(self.gmm_samples)
                    # print self.gmm_samples
                    gmm.fit(np.asarray(self.gmm_samples))
                    bic.append(gmm.bic(np.asarray(self.gmm_samples)))
                    if bic[-1] < lowest_bic:
                        lowest_bic = bic[-1]
                        self.sampling_gmm = gmm

                # print(bic)
                print(self.sampling_gmm.means_)
                print(self.sampling_gmm.covariances_)

                self.gmm_active = True
                print(self.gmm_samples)
                print(np.asarray(self.gmm_samples))
                print("GMM is active")

            print("Classifier is active")

    def _calculateMeanReward(self):
        counter = 0
        xsum = 0
        for i in range(0, len(self.rewards)):
            if self.success[i] == 1:
                counter += 1
                xsum += self.rewards[i]

        if counter == 0:
            return 0
        return xsum / counter

    def _preprocessSamples(self):
        for i in range(0, len(self.rewards)):
            if self.rewards[i] < self.mean:
                self.success[i] = 0

    def _checkSamples(self):
        counter = 0
        for i in range(0, len(self.svm_samples)):
            if self.rewards[i] >= self.mean:
                counter += 1
        return counter

    def _redefineSamples(self):
        self.gmm_samples = []
        for i in range(0, len(self.rewards)):
            if self.rewards[i] < self.mean:
                self.success[i] = 0
            else:
                self.success[i] = 1
                self.gmm_samples.append(self.svm_samples[i])

    def _terminate(self):
        pass

    def _is_learned(self) -> bool:
        if self.cnt_trial >= self.configuration.n_trials:
            return True
        return False
