import logging
from abc import ABCMeta
from abc import abstractmethod
import numpy as np
import copy
import time
from mongodb_client.mongodb_client import MongoDBClient
from knowledge_processor.knowledge_processor_base import KnowledgeProcessorBase


logger = logging.getLogger("ml_service")

class KnowledgeProcessor(KnowledgeProcessorBase):
    def __init__(self, vector_mapping, task_identity, mean_optimum_weights = None, sources = []):
        super().__init__(vector_mapping, task_identity, mean_optimum_weights, sources)

    def process_knowledge(self, successful_trials) -> list:
        '''process raw data from trials to knowledge; working from and on the database'''
        clusters = self.find_cluster(successful_trials)
        #use best cluster:
        if len(clusters) == 0:
            logger.error("KnowledgeProcessor.process_knowledge: No clusters found in data. Cant process knowledge.")
            return False

        successful_trials = clusters[0]

        #combine ml data -> knowledge (centroid):
        weights = np.log(len(successful_trials) + 0.5) - np.log(np.arange(1, len(successful_trials) + 1))
        weights /= sum(weights)  # weights like in CMA 'superlinear'
        data = []
        costs = []
        for trial in successful_trials:       
            trial_params_dict = trial["theta"]
            trial_params = self.dict_to_list(trial_params_dict)
            data.append(trial_params)
            costs.append(trial["cost"])
        centroid = np.dot(weights,data)
        expected_cost = float(np.dot(weights,costs))

        logger.debug("knowledge_processor: knowledge successful processed")
        return self.wrap_information(centroid,expected_cost)


    def get_raw_data(self, d):
        successful_trials = []
        for nr in range(len(d)):
            key = "n"+str(nr)
            if d.get(key,False):  # if trial number available
                if(d[key]["success"]==True):  # if trial was successfull
                    successful_trials.append(d[key])
        return successful_trials

    def dict_to_list(self, d):
        '''returns a list with dict contents'''
        l = []
        for key in d.keys():
            l.append(d[key])
        return l

    def find_cluster(self, data):
        def distance_to(a,b):
            '''distance between 2 multidimensional points'''
            return np.sqrt(sum((np.array(a)-np.array(b))**2))
        data = copy.deepcopy(data)
        logger.debug("ClusterProcessor: start working")
        clusters = []

        while data:
            #sort for cost
            c_list = sorted(data, key= lambda t: (t["cost"]))  #lowest cost first
            # sorted for distance to best trial:
            d_list = sorted(data, key= lambda t: distance_to(self.dict_to_list(t["theta"]),self.dict_to_list(c_list[0]["theta"])))
            cluster = [data.pop(data.index(d_list[0]))]
            for d_trial in d_list[1:]:
                mean_gradient = 0
                if len(cluster) >= 2:
                    for trial in cluster[1:]:
                        mean_gradient += (trial["cost"]-cluster[0]["cost"]) / distance_to(self.dict_to_list(trial["theta"]),self.dict_to_list(cluster[0]["theta"]))
                    mean_gradient = mean_gradient / len(cluster[1:])

                dist = distance_to(self.dict_to_list(d_trial["theta"]),self.dict_to_list(cluster[0]["theta"]))

                if d_trial["cost"] > cluster[-1]["cost"]:
                    cluster.append(data.pop(data.index(d_trial)))
                elif d_trial["cost"] > 0.8*dist*mean_gradient + cluster[0]["cost"]:
                    cluster.append(data.pop(data.index(d_trial)))
                else:
                    break
                
            clusters.append(cluster)

        return clusters
