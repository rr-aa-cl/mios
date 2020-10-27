import logging
from abc import ABCMeta
from abc import abstractmethod
import numpy as np
import copy
import time
from mongodb_client.mongodb_client import MongoDBClient

class KnowledgeProcessorBase(metaclass=ABCMeta):
    def __init__(self, vector_mapping, task_identity, mean_optimum_weights = None, confidence = None):
        self.vector_mapping = vector_mapping
        self.task_identity = task_identity
        self.mean_optimum_weights = mean_optimum_weights
        self.confidence = confidence

    @abstractmethod
    def process_knowledge(self, successful_trials) -> list:
        '''process raw data from trials to knowledge; working from and on the database -> returns centroid as list and expected cost as float'''
        raise NotImplementedError
    
    def wrap_information(self, centroid, expected_cost):
        #set up knowledge dict
        parameter_dict = {}

        for key_name, parameter in zip(self.vector_mapping, centroid):
            parameter_dict[key_name] = float(parameter)  # use python float because of rpc restrictions

        if self.task_identity.get("optimum_weights", False): 
            optimum_weights = self.task_identity["optimum_weights"]
        else:  # if knowledge is based on different tasks
            optimum_weights = self.mean_optimum_weights
        meta = dict()
        meta["expected_cost"] = expected_cost
        meta["optimum_weights"] = optimum_weights
        meta["geometry_factor"] = self.task_identity["geometry_factor"]
        meta["task_type"] = self.task_identity["task_type"]
        meta["tags"] = self.task_identity["tags"]
        meta["time"] = time.ctime()
        meta["confidence"] = self.confidence

        knowledge = {"parameters":parameter_dict, 
                     "meta": meta
                     }
        return knowledge

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
