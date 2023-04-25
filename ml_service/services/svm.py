import logging
import numpy as np
import random
import deap
import time
import json
from socket import timeout

from sklearn.svm import SVC
from sklearn import mixture
from sklearn.model_selection import KFold, cross_val_score

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
        self.batch_synchronisation = False
        self.request_probability = 0.0
        self.request_probability_decrease = False
        self.finish_cost = 0

    def __del__(self):
        print("DESTRUCTOR")

    def _to_dict(self):
        config = {
            "failure_base_cost": self.failure_base_cost,
            "n_trials": self.n_trials,
            "target_cost": self.target_cost,
            "batch_width": self.batch_width,
            "n_immigrant": self.n_immigrant,
            "batch_synchronisation": self.batch_synchronisation,
            "request_probability": self.request_probability,
            "request_probability_decrease": self.request_probability_decrease,
            "finish_cost": self.finish_cost
        }
        return config

    def _from_dict(self, config_dict):
        self.failure_base_cost = config_dict["failure_base_cost"]
        self.n_trials = config_dict["n_trials"]
        self.target_cost = config_dict["target_cost"]
        self.batch_width = config_dict["batch_width"]
        self.n_immigrant = config_dict["n_immigrant"]
        self.batch_synchronisation = config_dict["batch_synchronisation"]
        self.request_probability = config_dict["request_probability"]
        self.request_probability_decrease =config_dict["request_probability_decrease"]
        self.finish_cost = config_dict["finish_cost"]


class SVMService(BaseService):
    def __init__(self, mios_port=12000, mongo_port=27017):
        super(SVMService, self).__init__(mios_port, mongo_port)

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
        self.neglect_samples = 0
        self.bad_gmm_prediciton = 0

    def _initialize(self):
        self.numberOfParameters = 2
        self.sampleCounter=0
        self.cnt_trial=0
        self.cnt_batch=0
        self.globalcost=[]
        self.gmm_samples=[]
        self.bestSample=[]
        self.svmCounter=0
        self.neglect_samples = 0  # neglect first part of self.success, self.rewards to calculate self.mean
        self.bad_gmm_prediciton = 0  # counts how often gmm is not able to select samples which satisfy svm-predictions
        self.minCost=np.infty
        self.success=[]
        self.rewards=[]
        self.svm_samples=[]
        self.classifierActive=False
        self.gmm_active=False
        self.mean=0
        self.task_identity_name = self.problem_definition.get_identification_name()
        self.request_probability = self.configuration.request_probability

        self.episodes=int(self.configuration.n_trials/self.configuration.batch_width)

        self.limits = self.problem_definition.domain.limits
        self.kb = None
        self.engine.register_stop_condition(self._is_learned)

    def _learn_task(self):
        if self.knowledge:
            if self.knowledge.kb_location is not None:
                print("kb_location = ",self.knowledge.kb_location)
                self.kb = ServerProxy("http://" + self.knowledge.kb_location + ":8001")
        else:
            self.kb = None

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
            if self.minCost < self.configuration.finish_cost:
                break
            self._setSamples(self.cnt_batch)#done
            self._run_trial_par(self.action_list_norm)#td
            self._trainSVM()#td

        self.problem_data = {
            "parameters": self.bestSample,
            "cost": self.minCost,
            "success": True#?
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
        print("Evaluating batch " + str(self.cnt_batch))

        if self.configuration.batch_synchronisation:
            if self.kb is not None:
                while self.kb.wait_for_collective(self.host_name, int(self.cnt_batch)):
                    time.sleep(5)
            else:
                logger.error("SVM: Batch synchronisation is ON but no kb_location was set.")
        

        self.cnt_trial += self.configuration.batch_width

        trial_uuids = dict()

        x_set_external = []
        new_set = []
        if self.kb is not None and self.configuration.request_probability == 0 and self.configuration.n_immigrant > 0:
            while True:
                try:
                    new_set = self.kb.request_trials(str(self.task_identity_name), self.configuration.n_immigrant)  # new_set: list of tuples: [(Theta, Cost, Origin), ...]
                    break
                except timeout:
                    time.sleep(random.randint(5,10))
            if len(new_set) > 0:
                x_set_external = x_set[-len(new_set):]
                x_set = x_set[:-len(new_set)]
                for i in range(len(new_set)):   # checking for non_sharable parts of the parameter vector which would be not overwritten (don't used as default)
                    for j in range(len(new_set[i])):
                        if self.problem_definition.domain.vector_mapping[j] in self.problem_definition.domain.non_shareables:
                            print("Not sharing: " + self.problem_definition.domain.vector_mapping[j])
                            new_set[i][j] = x_set_external[i][j]
                for i in new_set:
                    x_set.append(i[0])
                    #costs.append((i[1],))    # we evaluate the cost on this robot again
                new_set.reverse()
        else:
            print("no external trials")

        
        x_set.reverse() # so the external trials come first
        
        costs = []
        self.success_ratio = 0
        if self.cnt_batch==0 and len(self.initial_knowledge_list)>0:
            len_first_batch = len(self.initial_knowledge_list)
            if len_first_batch < self.configuration.batch_width:
                len_first_batch = self.configuration.batch_width
            for i in range(len_first_batch):
                theta = []
                try:
                    external = self.initial_knowledge_list[i].identification_name
                    for key in self.initial_knowledge_list[i].parameters:
                        theta.append(self.initial_knowledge_list[i].parameters[key])
                    theta = self.problem_definition.domain.normalize(np.asarray(theta))
                except IndexError:
                    external = False
                    theta = x_set[i]
                try:
                    x_set[i] = theta
                except IndexError:
                    x_set.append(theta)
                uuid = self.push_trial(theta, external=external)
                trial_uuids[uuid] = theta
                ##same as below:
                result = self.wait_for_result(uuid)
                if result.q_metric.final_cost is None:
                    logger.error("None was returned as cost, invoking stop.")
                    self.stop()
                    costs.append((0,))
                else:
                    self.success_ratio += result.q_metric.success
                    costs.append((result.q_metric.final_cost,))
                print("result.q_metric.success: ",result.q_metric.success)
                if external:
                    if external not in self.external_success:
                        self.external_success[external] = [] 
                    self.external_success[external].append(int(result.q_metric.success))
                    self.similarity_estimate[external] = float(np.mean(self.external_success[external]))
                    if self.configuration.request_probability_decrease:  # calculate request probability
                        max_sim = max(self.similarity_estimate.values())
                        if self.request_probability > 0.5:
                            self.request_probability = self.request_probability * 0.96  # takes 17 external trial for request_probabiltiy of 1 to fall under 0.45
                        else:
                            if max_sim > 0:
                                if np.mean(self.internal_success)/max_sim > 1:  # internal trials are better than external
                                    self.request_probability = self.request_probability * 0.96
                                else:  #external trials are better
                                    self.request_probability = self.request_probability * 1.04
                            else:
                                self.request_probability = self.request_probability * 0.96
                else:
                    self.internal_success.append(result.q_metric.success)
                #if self.configuration.request_probability_decrease:
                #    max_sim = max(self.similarity_estimate.values())
                #    self.request_probability = np.tanh(max_sim*2.5)  # map the best similarity (0..1) to request probability
                if self.request_probability<0.01 and self.request_probability>0:
                    self.request_probability = 0.05
                if result.q_metric.success:
                    if self.kb is not None:
                        theta = []
                        for i in range(len(trial_uuids[uuid])):
                            theta.append(float(trial_uuids[uuid][i]))
                        while True:
                            try:
                                self.kb.push_trial(self.task_identity_name, theta, float(result.q_metric.final_cost), self.configuration.batch_width*5)
                                break
                            except timeout:
                                time.sleep(random.randint(5,10))
        else:
            for i in range(len(x_set)):
                external = False
                if i<len(x_set_external):  # mark the first trials as external (if n_immigrants is used, wont happen for request_probability)
                    external=new_set[i][2]  # agent name of trial origin
                print("\n\n request_probability",self.request_probability)
                if self.request_probability > 0:
                    if random.random() < self.request_probability:
                        print("requesting 1 trial with ", self.similarity_estimate, " \nfrom ",self.task_identity_name)
                        try:
                            new_trial = self.kb.request_trials(str(self.task_identity_name), 1, self.similarity_estimate)[0]  # take first Tuple of the list
                            external = new_trial[2]
                            uuid = self.push_trial(new_trial[0], external=external)
                        except IndexError:
                            print("request_trial was returning 0 trials")
                            uuid = self.push_trial(x_set[i], external=external)
                    else:
                        uuid = self.push_trial(x_set[i], external=external)
                else:
                    uuid = self.push_trial(x_set[i], external=external)  # evalutae the trials (->engine->mios)
                trial_uuids[uuid] = x_set[i]
                ##same as above:
                result = self.wait_for_result(uuid)
                if result.q_metric.final_cost is None:
                    logger.error("None was returned as cost, invoking stop.")
                    self.stop()
                    costs.append((0,))
                else:
                    self.success_ratio += result.q_metric.success
                    costs.append((result.q_metric.final_cost,))
                print("result.q_metric.success: ",result.q_metric.success)
                if external:
                    if external not in self.external_success:
                        self.external_success[external] = []
                    self.external_success[external].append(int(result.q_metric.success))
                    self.similarity_estimate[external] = float(np.mean(self.external_success[external]))
                    if self.configuration.request_probability_decrease:  # calculate request probability
                        max_sim = max(self.similarity_estimate.values())
                        if self.request_probability > (self.configuration.request_probability/2):
                            self.request_probability = self.request_probability * 0.93  
                        else:
                            if max_sim > 0:
                                if np.mean(self.internal_success)/max_sim > 1:  # internal trials are better than external
                                    self.request_probability = self.request_probability * 0.93
                                else:  #external trials are better
                                    self.request_probability = self.request_probability * 1.04
                            else: 
                                self.request_probability = self.request_probability * 0.93
                else:
                    self.internal_success.append(result.q_metric.success)
                if result.q_metric.success:
                    if self.kb is not None:
                        theta = []
                        for i in range(len(trial_uuids[uuid])):
                            theta.append(float(trial_uuids[uuid][i]))
                        while True:
                            try:
                                self.kb.push_trial(self.task_identity_name, theta, float(result.q_metric.final_cost), self.configuration.batch_width*5)
                                break
                            except timeout:
                                time.sleep(random.randint(5,10))
        for key in self.similarity_estimate:
            if self.similarity_estimate[key] <= 0:
                self.similarity_estimate[key] = 0.05  # small chance to sill get trials from this Task
        # for uuid in trial_uuids:
        #     result = self.wait_for_result(uuid)
        #     if result.q_metric.final_cost is None:
        #         logger.error("None was returned as cost, invoking stop.")
        #         self.stop()
        #         costs.append((0,))
        #     else:
        #         self.success_ratio += result.q_metric.success
        #         costs.append((result.q_metric.final_cost,))

        #     print("result.q_metric.success: ",result.q_metric.success)
        #     if result.q_metric.success:
        #         if self.kb is not None:
        #             theta = []
        #             for i in range(len(trial_uuids[uuid])):
        #                 theta.append(float(trial_uuids[uuid][i]))
        #             while True:
        #                 try:
        #                     self.kb.push_trial(self.task_identity_name, theta, float(result.q_metric.final_cost), self.configuration.batch_width*5)
        #                     break
        #                 except timeout:
        #                     time.sleep(random.randint(5,10))
        #             # kb.push_trial_2(theta, float(result.final_cost), self.problem_definition.cost_function.geometry_factor)

        self.success_ratio /= float(len(trial_uuids))

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
        self.cnt_batch += 1
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
                if not self.confidence:
                    self.confidence = 0.1
                self.action_list_norm.append([float(param) for param in self.centroid])  # add centroid ("knowledge") to action list
                for i in range(1,self.configuration.batch_width):  # fill up batch with random trials around centroid
                    random_trial = np.random.normal(0, self.confidence, self.numberOfParameters) + self.centroid
                    self.action_list_norm.append(list(random_trial))   
            else:
                temp_param_norm_samples = lhs(self.numberOfParameters, samples=self.configuration.batch_width)
                for t in temp_param_norm_samples:
                    self.action_list_norm.append(t)
            if self.knowledge.equal_start:
                logger.debug("svm._setSamples: searching for first batch to set equal starting conditions.")
                while True:
                    try:
                        result = self.kb.get_result("ml_results", self.problem_definition.skill_class, {"meta.tags": self.knowledge.equal_tags})
                        break
                    except timeout:
                        time.sleep(random.randint(5,10))
                if result:
                    if len(result.keys()) < (self.configuration.batch_width+2):
                        print("found result has no full batch size")
                        return
                    self.action_list_norm = []
                    for i in range(1,self.configuration.batch_width+1):
                        self.action_list_norm.append(self.problem_definition.domain.normalize(np.asarray(self.get_params(result["n"+str(i)]["theta"]))))
                    self.action_list_norm.reverse()
                else:
                    logger.debug("svm._setSamples: no equal starting batch size was found")
        else:
            while i < self.configuration.batch_width:
                if counter>=1000:
                    if self.gmm_active==True:
                        action_norm=self.getGmmSample()
                    else:
                        action_norm=np.random.uniform(0,1,self.numberOfParameters)

                    j=0
                    for a in action_norm:
                        if a<0:
                            action_norm[j]=0
                        if a>1:
                            action_norm[j]=1
                        j+=1

                    self.action_list_norm.append(action_norm)
                    i += 1
                    counter = 0
                    self.bad_gmm_prediciton += 1
                    continue

                elif self.classifierActive==True:
                    if self.gmm_active==True:
                        action_norm=self.getGmmSample()
                    else:
                        action_norm = np.random.uniform(0.0, 1.0, self.numberOfParameters)

                    j = 0
                    # print action_norm
                    for a in action_norm:
                        if a<0:
                            action_norm[j]=0
                        if a>1:
                            action_norm[j]=1
                        j+=1

                    aa=action_norm
                    aa=aa.reshape([1,-1])
                    prediction=self.classifier.predict(aa)
                    #print prediction

                    if prediction==1:
                        #raw_input("es passiert was!")
                        #print("accepted")
                        self.action_list_norm.append(action_norm)
                        i += 1

                    else:
                        #print(" rejected")
                        counter += 1
                        continue
                else:
                    action_norm=np.random.uniform(0.0,1.0,self.numberOfParameters)

                    j=0
                    #print action_norm
                    for a in action_norm:
                        if a<0:
                            action_norm[j]=0
                        if a>1:
                            action_norm[j]=1
                        j+=1

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
        self.svmCounter = sum(self.success)
        if self.svmCounter >= 5:
            if self.bad_gmm_prediciton >= self.configuration.batch_width:
                self.neglect_samples = len(self.rewards) - self.configuration.batch_width  # neglect everything bevor last (bad) batch when calculating self.mean
                self.mean = sum(self.rewards[self.neglect_samples:]) / len(self.rewards[self.neglect_samples:])
            self._preprocessSamples()
            self.mean = self._calculateMeanReward()
            self._redefineSamples()
            # raw_input (self.mean)

            # self.classifier.fit(self.svm_samples,self.success)

            #if self.neglect_samples > 0:
            #    print("sucess:",self.success,"\n","svm_samples:",self.svm_samples)
            
            # Kfold active:
            k_fold = KFold(n_splits=5)
            best_score = 0
            tt = 0
            for train, test in k_fold.split(self.svm_samples):
                if len(np.unique(np.asarray(self.success)[train])) > 1:  # number of classes has to be greater than 1
                    clf = SVC(C=100000)
                    clf.fit(np.asarray(self.svm_samples)[train], np.asarray(self.success)[train])
                    score = clf.score(np.asarray(self.svm_samples)[test],np.asarray(self.success)[test])
                    print("score = ",score)
                    print("descision_function: ", clf.decision_function(self.svm_samples))
                    if score > best_score:  # takes best score
                        best_score = score
                        temp = np.mean(np.abs(clf.decision_function(self.svm_samples)))
                        if tt < temp:  # takes best decision function mean
                            tt = temp
                            self.classifier = clf
                            self.classifierActive = True


            ## Kfold inactive:
            #if len(np.unique(np.asarray(self.success))) > 1:
            #    clf = SVC(C=100000)
            #    clf.fit(self.svm_samples, self.success)
            #    self.classifierActive = True
            #    temp = np.mean(np.abs(clf.decision_function(self.svm_samples)))
            #    tt = 0
            #    if tt < temp:
            #        tt = temp
            #        self.classifier = clf

            print("SVM active = ",self.classifierActive)
            if self.svmCounter >= 15 and len(self.gmm_samples) > 2:    # gmm_samples > mean

                for x in self.classifier.support_vectors_:
                    pass
                    # self.gmm_samples.append(x)

                lowest_bic = np.infty
                bic = []
                maxcomponents = 8
                if maxcomponents > len(self.gmm_samples):
                    maxcomponents = len(self.gmm_samples)
                #maxcomponents = 1
                self.sampling_gmm = mixture.BayesianGaussianMixture(n_components=maxcomponents, covariance_type='diag', n_init=3)
                self.sampling_gmm.fit(np.asarray(self.gmm_samples))

                self.gmm_active = True
                print(self.gmm_samples)
                print(np.asarray(self.gmm_samples))
                print("GMM is active")

            else:
                self.gmm_active = False

            print("Classifier is active")

    def _calculateMeanReward(self):
        counter = 0
        xsum = 0
        for i in range(0, len(self.rewards[self.neglect_samples:])):
            if self.success[self.neglect_samples + i] == 1:
                counter += 1
                xsum += self.rewards[self.neglect_samples + i]

        if counter == 0:
            return 0
        return xsum / counter

    def _preprocessSamples(self):
        for i in range(0, len(self.rewards)):
            if self.rewards[i] < self.mean:
                self.success[i] = 0
            else:
                self.success[i] = 1


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
