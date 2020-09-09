import logging
import numpy as np
from mongodb_client.mongodb_client import MongoDBClient
from sklearn.cluster import DBSCAN

import pprint

logger = logging.getLogger("ml_service")

class KnowledgeProcessor():
    def __init__(self, host='localhost', port=27017):
        self.DBclient = MongoDBClient(host, port)

    def process_knowledge(self, filter: dict, data_db: str, data_col: str, knowledge_db: str, knowledge_col: str):
        doc = self.DBclient.read(data_db, data_col, filter)
        #pprint.pprint(doc)
        if len(doc) > 1:
            logger.info("WARNING: process knowledge for more tasks")
        
        doc = doc[0]

        # get raw ml data:
        successful_trials = []
        for key, trial in doc.items():
            if key == "meta" or key == "_id":
                continue
            if(trial["success"]==True):
                successful_trials.append(trial)
        
        #sort for relevance:
        successful_trials = sorted(successful_trials, key= lambda t: (t["total_cost"]))
        #top10
        successful_trials = successful_trials[:10]
        
        #combine ml data -> knowledge (centroid):
        weights = np.log(len(successful_trials) + 0.5) - np.log(np.arange(1, len(successful_trials) + 1))
        weights /= sum(weights)  # weights like in CMA 'superlinear'
        data = []
        for trial in successful_trials:
            trial_params = []
            trial_params_dict = trial["theta"]
            for key in trial_params_dict.keys():
                trial_params.append(trial_params_dict[key])
            data.append(trial_params)
        centroid = np.dot(weights,data)

        #set up knowledge dict
        parameter_dict = {}
        for key_name, parameter in zip(doc["meta"]["domain"]["vector_mapping"], centroid):
            parameter_dict[key_name] = parameter

        meta = doc["meta"]
        meta.pop("uuid", None)
        meta.pop("t_0", None)
        meta.pop("date", None)
        meta["confidence"] = None

        knowledge = {"parameters":parameter_dict, 
                     "meta": meta
                     }
        #save knowledge on database
        knowledge_id = self.DBclient.write(knowledge_db, knowledge_col, knowledge)
        return knowledge_id


    def get_knowledge(self, filter, knowledge_db, knowledge_col):
        docs = self.DBclient.read(knowledge_db, knowledge_col, filter)
        if len(docs) >= 1:
            logger.debug("knowledge_processor.get_knowledge(): found knowledge " + str(docs[0]))
            return docs[0]
        else:
            logger.debug("knowledge_processor.get_knowledge(): found none! -> return None")
            return None

