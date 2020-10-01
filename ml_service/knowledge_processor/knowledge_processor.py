import logging
import numpy as np
import copy
import time
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
        self.data_db = "ml_results"
        self.knowledge_db = "knowledge"

    def process_knowledge(self, task_identity: dict, data_db:str = "ml_results", knowledge_db:str = "local_knowledge", knowledge_tags:list = []) -> str("_id"):
        '''process raw data from trials to knowledge; working from and on the database'''
        #allocate all ml_data with same task identity:
        result_filter = {  "meta.tags":task_identity["tags"],\
                    "meta.cost_function.optimum_weights":task_identity["optimum_weights"],\
                    "meta.task_type":task_identity["task_type"]
                 }

        doc = self.DBclient.read(data_db, task_identity["task_type"], result_filter)
        if doc is None or len(doc) == 0:
            logger.error("Could not find any results for filter " + str(result_filter) + " on database " + data_db + " in collection " + task_identity["task_type"] + ".")
            return False

        #save knowledge source
        uuids = []
        tags = set()
        for d in doc:
            uuids.append(d["meta"]["uuid"])
            for t in d["meta"]["tags"]:
                tags.add(t)

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
            metainfo.append(doc["meta"])

        for m in metainfo:
            if m["domain"]["vector_mapping"] != metainfo[0]["domain"]["vector_mapping"]:
                logger.error("knowledge_processor: got trials from different domains. Cant process them together")
        #find clusters:
        clusters = self.cluster_processor.find_cluster(successful_trials)
        #use best cluster:
        successful_trials = clusters[0]
        #use top 10 trials:
        #sort for cost
        #successful_trials = sorted(successful_trials, key= lambda t: (t["cost"]))  #lowest cost first
        #successful_trials = successful_trials[:10]

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
        #set up knowledge dict
        parameter_dict = {}

        for key_name, parameter in zip(metainfo[0]["domain"]["vector_mapping"], centroid):
            parameter_dict[key_name] = float(parameter)  # use python float because of rpc restrictions

        # save knoweldge_tags together tags from used data
        knowledge_tags.extend(list(tags))
        knowledge_tags = list(set(knowledge_tags))

        meta = metainfo[0]
        meta.pop("uuid", None)
        meta.pop("t_0", None)
        meta.pop("date", None)
        meta["confidence"] = None
        meta["knowledge_source"] = uuids
        meta["expected_cost"] = expected_cost
        meta["optimum_weights"] = task_identity["optimum_weights"]
        meta["task_type"] = task_identity["task_type"]
        meta["tags"] = task_identity["tags"]

        knowledge = {"parameters":parameter_dict, 
                     "meta": meta
                     }
        #save knowledge on database
        #check if knowledge to task_identitiy is already available:
        knowledge_filter = {"meta.tags": task_identity["tags"], \
                            "meta.task_type": task_identity["task_type"], \
                            "meta.optimum_weights": task_identity["optimum_weights"]}
        available_knowledge = self.DBclient.read(knowledge_db,task_identity["task_type"],knowledge_filter)
        if len(available_knowledge) == 0:
            logger.debug("knowlege_processor.process_knowledge: create new knowledge entry on "+str(knowledge_db)+" for task identity "+str(task_identity))
            return self.DBclient.write(knowledge_db, task_identity["task_type"], knowledge)
        elif len(available_knowledge) == 1:
            logger.debug("knowlege_processor.process_knowledge: update knowledge entry for task identity "+str(task_identity)+" on database "+str(knowledge_db))
            #self.DBclient.update(knowledge_db,task_identity["task_type"],{"_id":available_knowledge[0]["_id"]},knowledge)
            id = available_knowledge[0]["_id"]
            knowledge["_id"] = id
            self.DBclient.remove(knowledge_db,task_identity["task_type"],{"_id":id})
            self.DBclient.write(knowledge_db,task_identity["task_type"],knowledge)
            return available_knowledge[0]["_id"]
        else:
            logger.error("knowlege_processor.process_knowledge: Multiple knowledge entries found! Cannot decide which one to update")
            return False
        
    def process_knowledge_local(self, task_identity: dict, data_db: str = "ml_results") -> dict:
        '''process raw data from trials to knowledge; dont save knowledge to database'''
        #allocate all ml_data with same task identity:
        result_filter = {  "meta.tags":task_identity["tags"],\
                    "meta.cost_function.optimum_weights":task_identity["optimum_weights"],\
                    "meta.task_type":task_identity["task_type"]
                 }

        doc = self.DBclient.read(data_db, task_identity["task_type"], result_filter)
        if doc is None or len(doc) == 0:
            logger.error("Could not find any results for filter " + str(result_filter) + " on database " + data_db + " in collection " + task_identity["task_type"] + ".")
            return False
        #save knowledge source
        uuids = []
        tags = set()
        for d in doc:
            uuids.append(d["meta"]["uuid"])

        logger.debug("knowledge_processor: read raw data")
        metainfo = []
        if len(doc) >= 1:
            logger.info("WARNING: process knowledge for more tasks")

            alltrials = []
            for d in doc:
                metainfo.append(d["meta"])
                # get raw ml data:
                alltrials.extend(self.get_raw_data(d))
            successful_trials = alltrials
        if len(successful_trials) < 1:
            logger.error("knowledge_processor.proccess_knowledge_local(): No successful trials foud for knowledge generation!")
            return False

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
        costs = []
        for trial in successful_trials:       
            trial_params_dict = trial["theta"]
            trial_params = self.dict_to_list(trial_params_dict)
            data.append(trial_params)
            costs.append(trial["cost"])
        centroid = np.dot(weights,data)
        expected_cost = float(np.dot(weights,costs))

        logger.debug("knowledge_processor: knowledge successful processed")
        #set up knowledge dict
        parameter_dict = {}

        for key_name, parameter in zip(metainfo[0]["domain"]["vector_mapping"], centroid):
            parameter_dict[key_name] = float(parameter)  # use python float because of rpc restrictions

        meta = metainfo[0]
        meta.pop("uuid", None)
        meta.pop("t_0", None)
        meta.pop("date", None)
        meta["confidence"] = None
        meta["knowledge_source"] = uuids
        meta["expected_cost"] = expected_cost
        meta["optimum_weights"] = task_identity["optimum_weights"]
        meta["task_type"] = task_identity["task_type"]
        meta["tags"] = task_identity["tags"]

        knowledge = {"parameters":parameter_dict, 
                     "meta": meta
                     }

        return knowledge

    def get_local_knowledge(self, task_identity:dict, knowledge_db: str = "local_knowledge", data_db:str = "ml_results"):
        '''searches for most similar knowledge / creates knowledge from similar results'''
        collection = task_identity["task_type"]
        optimum_weights = task_identity["optimum_weights"]

        knowledge_filter = {  "meta.tags":task_identity["tags"],\
                    "meta.task_type":task_identity["task_type"]
                 }
        
        # search for knowldge from the same context (task_type, tags)
        docs = self.DBclient.read(knowledge_db, collection, knowledge_filter)
        if len(docs) >= 1:
            logger.debug("knowledge_processor.get_local_knowledge(): found knowledge on task identity" + str(task_identity) +" at "+str(knowledge_db)+"."+str(collection))
            # take most similar knowledge according to cost function ("optimum_weights"):
            return self.get_most_similar_task(optimum_weights,docs)

        logger.debug("knowledge_processor.get_local_knowledge(): found none! -> create local knowledge from ml data for task_identity"+str(task_identity))
        knowledge = self.process_knowledge_local(task_identity, data_db) 
        if knowledge:
            return knowledge

        logger.debug("knowledge_processor.get_local_knowledge(): found none! -> create knowledge from most similar ml data")
        docs = self.DBclient.read(data_db, collection, knowledge_filter)
        if len(docs) >= 1:
            return self.get_most_similar_task(optimum_weights,docs)

        logger.debug("knowledge_processor.get_local_knowledge(): no knowledge or ml data are available for task_type "+str(collection)+" with tags "+str(task_identity["tags"]))
        return False
                



    def get_ml_results(self, filter, data_col, data_db="ml_results"):
        ml_results = []
        retry_count = 0
        while len(ml_results) == 0:
            ml_results = self.DBclient.read(data_db,data_col,filter)
            retry_count +=1
            if retry_count >= 3:
                time.sleep(1)
                break
        return ml_results

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

    def get_most_similar_task(self, optimum_weights, tasks):
        '''find most similar task according to cost optimum_weights'''
        most_similar_task = None
        smallest_dist = float('inf')
        for task in tasks:
            if "cost_function" not in task.keys():
                logger.debug("knowledge_processor.get_most_similar_task: skipping old task format")
                continue
            # use euclidean distance as similarity measure:  sqrt(sum( (a-b)**2 ))
            dist = np.linalg.norm(np.array(optimum_weights)-np.array(task["meta"]["cost_function"]["optimum_weights"]))
            if dist < smallest_dist:
                smallest_dist = dist
                most_similar_task = task
        logger.debug("knowledge_processor.get_most_similar_task: found most similar task under "+str(len(tasks))+" tasks")
        return most_similar_task
