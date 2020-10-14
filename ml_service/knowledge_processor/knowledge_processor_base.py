import logging
from abc import ABCMeta
from abc import abstractmethod
import numpy as np
import copy
import time
from mongodb_client.mongodb_client import MongoDBClient

class KnowledgeProcessorBase(metaclass=ABCMeta):
    def __init__(self, vector_mapping, task_identity):
        self.vector_mapping = vector_mapping
        self.task_identity = task_identity

    @abstractmethod
    def process_knowledge(self, task_identity: dict, data_db:str = "ml_results", knowledge_db:str = "local_knowledge", knowledge_tags:list = []) -> list:
        '''process raw data from trials to knowledge; working from and on the database -> returns centroid as list and expected cost as float'''
        raise NotImplementedError
    
    def wrap_information(self, centroid, expected_cost):
        #set up knowledge dict
        parameter_dict = {}

        for key_name, parameter in zip(self.vector_mapping, centroid):
            parameter_dict[key_name] = float(parameter)  # use python float because of rpc restrictions


        meta = dict()
        meta["expected_cost"] = expected_cost
        meta["optimum_weights"] = self.task_identity["optimum_weights"]
        meta["task_type"] = self.task_identity["task_type"]
        meta["tags"] = self.task_identity["tags"]
        meta["time"] = time.ctime()

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
