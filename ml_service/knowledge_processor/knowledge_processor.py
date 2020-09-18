import logging
import numpy as np
import copy
from mongodb_client.mongodb_client import MongoDBClient
from sklearn.cluster import DBSCAN

import pprint

logger = logging.getLogger("ml_service")

class ClusterProcessor():
    
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


        #for i,cluster in enumerate(clusters):
        #    print("cluster",i," length:",len(cluster))
        #    for trial in cluster:
        #        print(trial["cost"])
        #    print("\n")
        return clusters

    def rank_cluster(self, clusters):
        '''rank the clusters according to reliability'''
        logger.debug("Cluster ranking according to reliability NOT implemented!")
        return clusters

class KnowledgeProcessor():
    def __init__(self, host='localhost', port=27017):
        self.DBclient = MongoDBClient(host, port)
        self.cluster_processor = ClusterProcessor()

    def process_knowledge(self, filter: dict, data_db: str, data_col: str, knowledge_db: str, knowledge_col: str, knowledge_tags:dict):
        '''process raw data from trials to knowledge; working from and on the database'''
        #allocate data:
        doc = self.DBclient.read(data_db, data_col, filter)
        #save knowledge source
        uuids = []
        for d in doc:
            uuids.append(d["meta"]["uuid"])
        logger.debug("knowledge_processor: read raw data")
        metainfo = []
        if len(doc) > 1:
            logger.info("WARNING: process knowledge for more tasks")

            alltrials = []
            for d in doc:
                metainfo.append(d["meta"])
                # get raw ml data:
                trials = self.get_raw_data(d)
                for t in trials:
                    alltrials.append(t)
            successful_trials = alltrials
        else:
            doc = doc[0]
            # get raw ml data:
            successful_trials = self.get_raw_data(doc)
        
        for m in metainfo:
            if m["domain"]["vector_mapping"] != metainfo[0]["domain"]["vector_mapping"]:
                logger.error("knowledge_processor: got trials from different domains. Cant process them together")
        #find clusters:
        clusters = self.cluster_processor.find_cluster(successful_trials)
        #use best cluster:
        successful_trials = clusters[0]
        
        #combine ml data -> knowledge (centroid):
        weights = np.log(len(successful_trials) + 0.5) - np.log(np.arange(1, len(successful_trials) + 1))
        weights /= sum(weights)  # weights like in CMA 'superlinear'
        data = []
        for trial in successful_trials:       
            trial_params_dict = trial["theta"]
            trial_params = self.dict_to_list(trial_params_dict)
            data.append(trial_params)
        centroid = np.dot(weights,data)

        #set up knowledge dict
        parameter_dict = {}

        for key_name, parameter in zip(metainfo[0]["domain"]["vector_mapping"], centroid):
            parameter_dict[key_name] = parameter

        meta = metainfo[0]
        meta.pop("uuid", None)
        meta.pop("t_0", None)
        meta.pop("date", None)
        meta["confidence"] = None
        meta["knowledge_source"] = uuids
        meta["tags"] = knowledge_tags

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



    def get_raw_data(self, d):
        successful_trials = []
        for key, trial in d.items():
            if key == "meta" or key == "_id":
                continue
            if(trial["success"]==True):
                successful_trials.append(trial)
        return successful_trials

    def dict_to_list(self, d):
        '''returns a list with dict contents'''
        l = []
        for key in d.keys():
            l.append(d[key])
        return l