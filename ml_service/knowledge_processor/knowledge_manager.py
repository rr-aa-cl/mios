import logging
import numpy as np
import copy
import time
from mongodb_client.mongodb_client import MongoDBClient
from knowledge_processor.knowledge_processor_v2 import KnowledgeProcessor
from knowledge_processor.kg_linear_regression import KGLinearRegressor
from sklearn.cluster import DBSCAN

logger = logging.getLogger("ml_service")

class KnowledgeManager():
    def __init__(self, host='localhost', port=27017):
        self.DBclient = MongoDBClient(host, port)
        self.data_db = "ml_results"
        self.knowledge_db = "local_knowledge"
        self.predictor = KGLinearRegressor()

    def collect_data(self, task_identity, data_db:str = "ml_results") -> list:
        if data_db.find("knowledge") == -1:  #  if collecting raw data (no knowledge)
            result_filter = {   "meta.tags":task_identity["tags"],\
                                "meta.cost_function.optimum_weights":task_identity["optimum_weights"],\
                                "meta.task_type":task_identity["task_type"]}
        else:  # if collecting knowledge:
            if "optimum_weights" in task_identity:  
                result_filter = {   "meta.tags":task_identity["tags"],\
                                    "meta.optimum_weights":task_identity["optimum_weights"],\
                                    "meta.task_type":task_identity["task_type"]}    
            else:
                result_filter = {   "meta.tags":task_identity["tags"],\
                                    "meta.task_type":task_identity["task_type"]}  


        doc = self.DBclient.read(data_db, task_identity["task_type"], result_filter)
        if doc is None or len(doc) == 0:
            logger.error("Could not find any results for filter " + str(result_filter) + " on database " + data_db + " in collection " + task_identity["task_type"] + ".")
            return False
        return doc



    def store_knowledge(self, knowledge, knowledge_db = "local_knowledge") -> str:
        knowledge_filter = {"meta.tags": knowledge["meta"]["tags"], \
                            "meta.task_type": knowledge["meta"]["task_type"], \
                            "meta.optimum_weights": knowledge["meta"]["optimum_weights"]}
        available_knowledge = self.DBclient.read(knowledge_db,knowledge["meta"]["task_type"],knowledge_filter)
        if len(available_knowledge) == 0:
            logger.debug("KnowledgeManager.store_knowledge: create new knowledge entry")
            return self.DBclient.write(knowledge_db, knowledge["meta"]["task_type"], knowledge)
        elif len(available_knowledge) == 1:
            logger.debug("KnowledgeManager.store_knowledge: update knowledge entry for task identity on database "+str(knowledge_db))
            id = available_knowledge[0]["_id"]
            knowledge["_id"] = id
            self.DBclient.remove(knowledge_db,knowledge["meta"]["task_type"],{"_id":id})
            self.DBclient.write(knowledge_db,knowledge["meta"]["task_type"],knowledge)
            return available_knowledge[0]["_id"]
        else:
            logger.error("KnowledgeManager.store_knowledge: Multiple knowledge entries found! Cannot decide which one to update")
            return False

    def process_knowledge(self, task_identity: dict, data_db:str = "ml_results", knowledge_db:str = "local_knowledge") -> str("_id"):
        '''process raw data from trials to knowledge; working from and on the database'''
        #allocate all ml_data with same task identity:
        doc = self.collect_data(task_identity, data_db)

        #save knowledge source
        uuids = []
        tags = set()
        for d in doc:
            uuids.append(d["meta"]["uuid"])
            
        successful_trials, vector_mapping = self.get_successful_trials(doc)
        #process knowledge:
        self.knowledge_processor = KnowledgeProcessor(vector_mapping,task_identity)
        knowledge = self.knowledge_processor.process_knowledge(successful_trials)

        knowledge["meta"]["knowledge_source"] = uuids
        knowledge["meta"]["prediction"] = False

        return self.store_knowledge(knowledge,knowledge_db)

    def process_knowledge_local(self, task_identity: dict, data_db:str = "ml_results") -> str("_id"):
        '''process raw data from trials to knowledge; working from and on the database'''
        #allocate all ml_data with same task identity:
        doc = self.collect_data(task_identity, data_db)

        #save knowledge source
        uuids = []
        tags = set()
        for d in doc:
            uuids.append(d["meta"]["uuid"])
            
        successful_trials, vector_mapping = self.get_successful_trials(doc)
        #process knowledge:
        self.knowledge_processor = KnowledgeProcessor(ector_mapping,task_identity)
        knowledge = self.knowledge_processor.process_knowledge(successful_trials)

        knowledge["meta"]["knowledge_source"] = uuids
        knowledge["meta"]["prediction"] = False

        return knowledge

    def get_training_data(self,docs):
        training_data_x = []
        training_data_y = []
        for doc in docs:
            if doc["meta"].get("optimum_weights", True):
                logger.error("KnowledgeManager: found invalid knowledge (no key \"optimum_weights\" in meta)")
            training_data_x.append(np.array(doc["meta"]["optimum_weights"]))
            training_data_y.append(np.array(self.dict_to_list(doc["parameters"])))
        return np.array(training_data_x), np.array(training_data_y)

    def predict_knowledge(self, task_identity:dict, knowledge_db: str = "local_knowledge"):
        '''trains and uses model to predict knolwedge'''
        #search for all tasks of same tasktype
        task_filter = copy.deepcopy(task_identity)
        task_filter.pop("optimum_weights")
        doc = self.collect_data(task_filter, knowledge_db)

        if not doc:  # if no predictions can be made: use similar knowledge
            logger.error("KnowledgeManager: Cant find knowledge for predictions ("+str(task_filter)+" on "+str(knowledge_db)+")")
            logger.debug("KnowledgeManager: Using similar Knowledge")
            if knowledge_db.find("global") == -1:
                data_db = "ml_results"
            else:
                data_db = "global_ml_results"
            return self.get_local_knowledge(task_identity, knowledge_db, data_db)

        # check if knowledge fits together:
        vector_mapping = doc[0]["parameters"].keys()
        for d in doc:
            if vector_mapping != d["parameters"].keys():
                logger.error("KnowledgeManager.predict_knowledge: found knowledge doesnt fit together: different vector mappings!")
                return False
        # traun
        training_data = self.get_training_data(doc)
        self.predictor.fit_data(training_data[0], training_data[1])
        # predict
        predict_x = np.array(task_identity["optimum_weights"])
        prediction = self.predictor.predict_data(predict_x)[0]
        # pack information together
        parameter_dict = {}
        for key_name, parameter in zip(vector_mapping, prediction):
            print(parameter)
            parameter_dict[key_name] = float(parameter)  # use python float because of rpc restrictions
        meta = dict()
        meta["expected_cost"] = False
        meta["optimum_weights"] = task_identity["optimum_weights"]
        meta["task_type"] = task_identity["task_type"]
        meta["tags"] = task_identity["tags"]
        meta["time"] = time.ctime()
        meta["prediction"] = True

        knowledge = {"parameters":parameter_dict, 
                     "meta": meta}
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

        logger.debug("knowledge_processor.get_local_knowledge(): found none! -> create knowledge from most similar ml data of task type " + str(collection))
        docs = self.DBclient.read(data_db, collection, knowledge_filter)
        if len(docs) >= 1:
            return self.get_most_similar_task(optimum_weights,docs)
        
        logger.debug("knowledge_processor.get_local_knowledge(): found no ml data of task type " + str(collection) +" -> search for different task types")
        knowledge_filter = {  "meta.tags":task_identity["tags"]}   
        docs = []  
        for col in self.DBclient.get_collections(self.knowledge_db):
            docs.extend(self.DBclient.read(data_db, col, knowledge_filter))
        if len(docs) >= 1:
            return self.get_most_similar_task(optimum_weights,docs)

        logger.debug("knowledge_processor.get_local_knowledge(): no knowledge or ml data are available for task_type "+str(collection)+" with tags "+str(task_identity["tags"]))
        return False
    
    def get_successful_trials(self, doc):
        metainfo = []
        if len(doc) > 1:
            logger.info("WARNING: process knowledge from more tasks")

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
        vector_mapping = metainfo[0]["domain"]["vector_mapping"]
        return successful_trials, vector_mapping

    def get_most_similar_task(self, optimum_weights, tasks):
        '''find most similar task according to cost optimum_weights'''
        most_similar_task = None
        smallest_dist = float('inf')
        for task in tasks:
            temp_optimum_weights = None
            if "cost_function" in task["meta"].keys():
                temp_optimum_weights = task["meta"]["cost_function"]["optimum_weights"]
            elif "optimum_weights" in task["meta"].keys():
                temp_optimum_weights = task["meta"]["optimum_weights"]
            else:
                logger.debug("knowledge_processor.get_most_similar_task: skipping faulty task format")
                continue

            # use euclidean distance as similarity measure:  sqrt(sum( (a-b)**2 ))
            dist = np.linalg.norm(np.array(optimum_weights)-np.array(temp_optimum_weights))

            if dist < smallest_dist:
                smallest_dist = dist
                most_similar_task = task

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
