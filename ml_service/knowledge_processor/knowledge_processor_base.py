from abc import ABCMeta
from abc import abstractmethod
import time

from services.knowledge import Knowledge


class KnowledgeProcessorBase(metaclass=ABCMeta):
    def __init__(self, vector_mapping, task_identfier, mean_optimum_weights = None, confidence = None):
        self.vector_mapping = vector_mapping
        self.task_identfier = task_identfier
        self.mean_optimum_weights = mean_optimum_weights
        self.confidence = confidence

    @abstractmethod
    def process_knowledge(self, successful_trials) -> dict or None:
        '''process raw data from trials to knowledge; working from and on the database -> returns centroid as list and expected cost as float'''
        raise NotImplementedError
    
    def wrap_information(self, centroid, expected_cost) -> dict:
        #set up knowledge dict
        parameter_dict = {}

        for key_name, parameter in zip(self.vector_mapping, centroid):
            parameter_dict[key_name] = float(parameter)  # use python float because of rpc restrictions

        knowledge = Knowledge()
        knowledge.parameters = parameter_dict
        knowledge.expected_cost = expected_cost
        knowledge.identity = self.task_identfier["identity"]
        knowledge.skill_class = self.task_identfier["skill_class"]
        knowledge.tags = self.task_identfier["tags"]
        knowledge.time = time.ctime()
        knowledge.confidence = self.confidence
        print("knowledge_procsessing: wrap_informtaion: ", knowledge.to_dict())
        return knowledge.to_dict()

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
