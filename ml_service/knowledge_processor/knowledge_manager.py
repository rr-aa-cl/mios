import logging
import numpy as np
import copy
import time
import random
from mongodb_client.mongodb_client import MongoDBClient
from knowledge_processor.knowledge_processor_v2 import KnowledgeProcessor
from knowledge_processor.kg_random_forest import KGRandomForest
from knowledge_processor.knowledge_generalizer_base import KnowledgeGeneralizerBase


logger = logging.getLogger("ml_service")


class KnowledgeManager():
    def __init__(self, host='localhost', port=27017):
        self.DBclient = MongoDBClient(host, port)
        self.data_db = "ml_results"
        self.knowledge_db = "local_knowledge"
        self.predictor = None
        self.validation_per = 0.2
        self.n_retrain = 10  # how many times the generalizer is retrained bevor prediction

    def collect_data(self, task_identity, data_db: str = "ml_results") -> list:
        if data_db.find("knowledge") == -1:  # if collecting raw data (no knowledge)
            if "optimum_weights" in task_identity:
                result_filter = {"meta.tags": task_identity["tags"],
                                "meta.cost_function.optimum_weights": task_identity["optimum_weights"],
                                "meta.cost_function.geometry_factor": task_identity["geometry_factor"],
                                "meta.task_type": task_identity["task_type"]}
            else:
                result_filter = {"meta.tags": task_identity["tags"],
                                "meta.task_type": task_identity["task_type"]}
        else:  # if collecting knowledge:
            if "optimum_weights" in task_identity:
                result_filter = {"meta.tags": task_identity["tags"],
                                 "meta.optimum_weights": task_identity["optimum_weights"],
                                 "meta.task_type": task_identity["task_type"]}
            else:
                result_filter = {"meta.tags": task_identity["tags"],
                                 "meta.task_type": task_identity["task_type"]}

        doc = self.DBclient.read(data_db, task_identity["task_type"], result_filter)
        if doc is None or len(doc) == 0:
            logger.error("Could not find any results for filter " + str(
                result_filter) + " on database " + data_db + " in collection " + task_identity["task_type"] + ".")
            return False
        return doc

    def store_knowledge(self, knowledge, knowledge_db="local_knowledge") -> str:
        if knowledge is None:
            return False
        knowledge_filter = {"meta.tags": knowledge["meta"]["tags"],
                            "meta.task_type": knowledge["meta"]["task_type"],
                            "meta.optimum_weights": knowledge["meta"]["optimum_weights"],
                            "meta.geometry_factor": knowledge["meta"]["geometry_factor"]}
        available_knowledge = self.DBclient.read(knowledge_db, knowledge["meta"]["task_type"], knowledge_filter)
        if len(available_knowledge) == 0:
            logger.debug("KnowledgeManager.store_knowledge: create new knowledge entry")
            return self.DBclient.write(knowledge_db, knowledge["meta"]["task_type"], knowledge)
        elif len(available_knowledge) == 1:
            logger.debug(
                "KnowledgeManager.store_knowledge: update knowledge entry for task identity on database " + str(
                    knowledge_db))
            id = available_knowledge[0]["_id"]
            knowledge["_id"] = id
            self.DBclient.remove(knowledge_db, knowledge["meta"]["task_type"], {"_id": id})
            self.DBclient.write(knowledge_db, knowledge["meta"]["task_type"], knowledge)
            return available_knowledge[0]["_id"]
        else:
            logger.error(
                "KnowledgeManager.store_knowledge: Multiple knowledge entries found! Cannot decide which one to update")
            return False

    def process_knowledge(self, task_identity: dict, data_db: str = "ml_results",
                          knowledge_db: str = "local_knowledge") -> str("_id"):
        '''process raw data from trials to knowledge; working from and on the database'''
        # allocate all ml_data with same task identity:
        doc = self.collect_data(task_identity, data_db)
        if not doc:
            return False
        # save knowledge source
        uuids = []
        tags = set()
        for d in doc:
            uuids.append(d["meta"]["uuid"])

        successful_trials, vector_mapping, mean_optimum_weights, confidence = self.get_successful_trials(doc)
        # process knowledge:
        self.knowledge_processor = KnowledgeProcessor(vector_mapping, task_identity, mean_optimum_weights, confidence)
        knowledge = self.knowledge_processor.process_knowledge(successful_trials)

        if not knowledge:
            logger.error("KnowledgeManager.process_knowledge: Knowledge cant be processed!")
            return False

        knowledge["meta"]["knowledge_source"] = uuids
        knowledge["meta"]["prediction"] = False

        return self.store_knowledge(knowledge, knowledge_db)

    def process_knowledge_local(self, task_identity: dict, data_db: str = "ml_results") -> str("_id"):
        '''process raw data from trials to knowledge; working from and on the database'''
        # allocate all ml_data with same task identity:
        doc = self.collect_data(task_identity, data_db)
        if not doc:
            return False
        # save knowledge source
        uuids = []
        tags = set()
        for d in doc:
            uuids.append(d["meta"]["uuid"])

        successful_trials, vector_mapping = self.get_successful_trials(doc)
        # process knowledge:
        self.knowledge_processor = KnowledgeProcessor(vector_mapping, task_identity)
        knowledge = self.knowledge_processor.process_knowledge(successful_trials)

        knowledge["meta"]["knowledge_source"] = uuids
        knowledge["meta"]["prediction"] = False

        return knowledge

    def get_learning_data(self, docs):
        training_data_x = []
        training_data_y = []
        for doc in docs:
            if not doc["meta"].get("optimum_weights", False):
                logger.error("KnowledgeManager: found invalid knowledge (no key \"optimum_weights\" in meta)")
                continue
            training_data_x.append(np.append(np.array(doc["meta"]["geometry_factor"]), np.array(doc["meta"]["optimum_weights"])))
            training_data_y.append(np.array(self.dict_to_list(doc["parameters"])))
        if len(training_data_x) < 1 or len(training_data_y) < 1:
            logger.error(
                "KnowledgeManager.predict_knowledge: Training or Validation data is too small (smaller than 1)")
            return False
        return np.array(training_data_x), np.array(training_data_y)
    
    def get_cost_from_data(self, docs):
        cost_data = []
        for doc in docs:
            if not doc["meta"].get("optimum_weights", False):
                logger.error("KnowledgeManager: found invalid knowledge (no key \"optimum_weights\" in meta)")
                continue
            cost_data.append(np.array(doc["meta"]["expected_cost"]))
        if len(cost_data) < 1:
            logger.error(
                "KnowledgeManager.predict_knowledge: Training or Validation data is too small (smaller than 1)")
            return False
        return np.array(cost_data)

    def get_predictor(self):
        if self.predictor is not None:
            return self.get_predictor
        else:
            return KGRandomForest()

    def predict_knowledge(self, task_identity: dict, knowledge_db: str = "local_knowledge",
                          predictor: KnowledgeGeneralizerBase = None):
        '''trains and uses model to predict knolwedge'''
        # search for all tasks of same tasktype
        task_filter = copy.deepcopy(task_identity)
        if "optimum_weights" in task_filter:  # search for all task, independend of optimum weights
            task_filter.pop("optimum_weights")
        if "geometry_factor" in task_filter:
            task_filter.pop("geometry_factor")
        if knowledge_db.find("global") == -1:  # if ml_results are needed, which one to use
            data_db = "ml_results"
        else:    
            data_db = "global_ml_results"

        doc = self.collect_data(task_filter, knowledge_db)

        if not doc:
            logger.error("KnowledgeManager: Cant find knowledge for predictions (" + str(task_filter) + " on " + str(
                knowledge_db) + ")")
            logger.debug("KnowledgeManager: Using similar Knowledge")
            return self.get_local_knowledge(task_identity, knowledge_db, data_db)
        # check if knowledge fits together:
        vector_mapping = doc[0]["parameters"].keys()
        for d in doc:
            if vector_mapping != d["parameters"].keys():
                logger.error(
                    "KnowledgeManager.predict_knowledge: found knowledge doesnt fit together: different vector mappings!")
                return False
        if len(doc) < 2:  # if no predictions can be made: use similar knowledge
            logger.error("KnowledgeManager: Cant find knowledge for predictions (" + str(task_filter) + " on " + str(
                knowledge_db) + ")")
            logger.debug("KnowledgeManager: Using similar Knowledge")
            return self.get_local_knowledge(task_identity, knowledge_db, data_db)

        # get best predictor:
        if predictor is None:
            predictor = self.get_predictor()

        # retrain the knowledge generalizer and take the best one
        best_predictor = predictor
        best_error = float("inf")
        for i in range(0, self.n_retrain):
            # divide into training-data and validation-data
            validation_size = int(len(doc) * self.validation_per)
            if validation_size < 1 and len(doc) > 1:
                validation_size = 1
            validation_set = []
            for i in range(0, validation_size):
                random_pic = random.randint(0, len(doc) - 1)
                validation_set.append(doc.pop(random_pic))

            # get learning data
            training_data = self.get_learning_data(doc)
            validation_data = self.get_learning_data(validation_set)
            if not (training_data and validation_data):  # sth went wrong, sets too small
                logger.debug("KnowledgeManager.predict_knowledge: Error in training or validation set -> use similar knowledge")
                return self.get_local_knowledge(task_identity,knowledge_db)

            # stadardize learning data
            std_deviation_data_y = np.std(np.append(validation_data[1], training_data[1], axis=0), axis=0)
            std_deviation_data_y = np.array(
                [1 if n == 0 else n for n in std_deviation_data_y])  # remove zeros from standard deviation
            std_deviation_data_x = np.std(np.append(validation_data[0], training_data[0], axis=0), axis=0)
            std_deviation_data_x = np.array(
                [1 if n == 0 else n for n in std_deviation_data_x])  # remove zeros from standard deviation
            mean_data_y = np.mean(np.append(validation_data[1], training_data[1], axis=0), axis=0)
            mean_data_x = np.mean(np.append(validation_data[0], training_data[0], axis=0), axis=0)
            training_data_y_normalized = (training_data[1] - mean_data_y) / std_deviation_data_y
            validation_data_y_normalized = (validation_data[1] - mean_data_y) / std_deviation_data_y
            training_data_x_normalized = (training_data[0] - mean_data_x) / std_deviation_data_x
            validation_data_x_normalized = (validation_data[0] - mean_data_x) / std_deviation_data_x

            # train
            predictor.fit_data(training_data_x_normalized, training_data_y_normalized)
            # validate
            if len(validation_data) > 0:
                distances = []
                for i in range(0, validation_size):
                    prediction = predictor.predict_data(validation_data_x_normalized[i])
                    distances.append(np.linalg.norm(prediction - validation_data_y_normalized[i]))
                error_in_context = float(
                    np.mean(distances))  # devide by the standard deviation to set the error into context
            else:
                error_in_context = False
            
            if error_in_context < best_error:
                best_predictor = copy.deepcopy(predictor)
                best_error = error_in_context
        predictor = best_predictor

        # predict
        predict_x = np.append(np.array(task_identity["geometry_factor"]), np.array(task_identity["optimum_weights"]))
        print("predict_x: " + str(predict_x))
        predict_x_normalized = (predict_x - mean_data_x) / std_deviation_data_x
        print("mean_data_x: " + str(mean_data_x))
        print("std_deviation_data_x: " + str(std_deviation_data_x))
        print("predict_x_normalized: " + str(predict_x_normalized))
        prediction_normalized = predictor.predict_data(predict_x_normalized)[0]
        prediction = (prediction_normalized * std_deviation_data_y) + mean_data_y

        # predict expected cost
        predictor.fit_data(training_data_x_normalized, self.get_cost_from_data(doc))
        print("##############################")
        print(predict_x_normalized)
        expected_cost = predictor.predict_data(predict_x_normalized)
        print(expected_cost)
        print(expected_cost[0])

        # pack information together
        parameter_dict = {}
        for key_name, parameter in zip(vector_mapping, prediction):
            parameter_dict[key_name] = float(parameter)  # use python float because of rpc restrictions
        meta = dict()
        meta["expected_cost"] = float(expected_cost[0])
        meta["prediction_error"] = error_in_context
        meta["optimum_weights"] = task_identity["optimum_weights"]
        meta["geometry_factor"] = task_identity["geometry_factor"]
        meta["task_type"] = task_identity["task_type"]
        meta["tags"] = task_identity["tags"]
        meta["time"] = time.ctime()
        meta["prediction"] = True

        knowledge = {"parameters": parameter_dict,
                     "meta": meta}

        return knowledge

    def get_local_knowledge(self, task_identity: dict, knowledge_db: str = "local_knowledge",
                            data_db: str = "ml_results"):
        '''searches for most similar knowledge / creates knowledge from similar results'''
        collection = task_identity["task_type"]
        optimum_weights = task_identity["optimum_weights"]

        knowledge_filter = {"meta.tags": task_identity["tags"], \
                            "meta.task_type": task_identity["task_type"]
                            }

        # search for knowldge from the same context (task_type, tags)
        docs = self.DBclient.read(knowledge_db, collection, knowledge_filter)
        if len(docs) >= 1:
            logger.debug("knowledge_processor.get_local_knowledge(): found knowledge on task identity" + str(
                task_identity) + " at " + str(knowledge_db) + "." + str(collection))
            # take most similar knowledge according to cost function ("optimum_weights"):
            return self.get_most_similar_task(optimum_weights, docs)

        logger.debug(
            "knowledge_processor.get_local_knowledge(): found none! -> create local knowledge from ml data for task_identity" + str(
                task_identity))
        knowledge = self.process_knowledge_local(task_identity, data_db)
        if knowledge:
            return knowledge

        logger.debug(
            "knowledge_processor.get_local_knowledge(): found none! -> create knowledge from most similar ml data of task type " + str(
                collection))
        docs = self.DBclient.read(data_db, collection, knowledge_filter)
        if len(docs) >= 1:
            return self.get_most_similar_task(optimum_weights, docs)

        logger.debug("knowledge_processor.get_local_knowledge(): found no ml data of task type " + str(
            collection) + " -> search for different task types")
        knowledge_filter = {"meta.tags": task_identity["tags"]}
        docs = []
        for col in self.DBclient.get_collections(self.knowledge_db):
            docs.extend(self.DBclient.read(data_db, col, knowledge_filter))
        if len(docs) >= 1:
            return self.get_most_similar_task(optimum_weights, docs)

        logger.debug(
            "knowledge_processor.get_local_knowledge(): no knowledge or ml data are available for task_type " + str(
                collection) + " with tags " + str(task_identity["tags"]))
        return False

    def get_successful_trials(self, doc):
        metainfo = []
        optimum_weights = []
        confidence = None
        if len(doc) > 1:
            logger.info("WARNING: process knowledge from more tasks")
            alltrials = []
            for d in doc:
                metainfo.append(d["meta"])
                # get raw ml data:
                trials = self.get_raw_data(d)
                if len(trials) > 0:
                    optimum_weights.append(d["meta"]["cost_function"]["optimum_weights"])
                for t in trials:
                    alltrials.append(t)
            successful_trials = alltrials
            optimum_weights = list(np.mean(optimum_weights, axis=0))
        else:
            doc = doc[0]
            # get raw ml data:
            successful_trials = self.get_raw_data(doc)
            metainfo.append(doc["meta"])
            confidence = doc["final_results"].get("confidence")

        for m in metainfo:
            if m["domain"]["vector_mapping"] != metainfo[0]["domain"]["vector_mapping"]:
                logger.error("knowledge_processor: got trials from different domains. Cant process them together")
        vector_mapping = metainfo[0]["domain"]["vector_mapping"]
        return successful_trials, vector_mapping, optimum_weights, confidence

    def get_most_similar_task(self, optimum_weights, tasks):
        '''find most similar task according to cost optimum_weights'''
        most_similar_task = tasks[0]
        smallest_dist = float('inf')
        for task in tasks:
            temp_optimum_weights = None
            if "cost_function" in task["meta"].keys():
                temp_optimum_weights = task["meta"]["cost_function"]["optimum_weights"]
            elif "optimum_weights" in task["meta"].keys():
                temp_optimum_weights = task["meta"]["optimum_weights"]
            else:
                logger.debug("knowledge_processor.get_most_similar_task: skipping faulty task format (cant find optimum_weights in task)")
                continue

            # use euclidean distance as similarity measure:  sqrt(sum( (a-b)**2 ))
            dist = np.linalg.norm(np.array(optimum_weights) - np.array(temp_optimum_weights))

            if dist < smallest_dist:
                smallest_dist = dist
                most_similar_task = task
        return most_similar_task

    def get_raw_data(self, d):
        successful_trials = []
        for nr in range(len(d)):
            key = "n" + str(nr)
            if d.get(key, False):  # if trial number available
                if (d[key]["success"] == True):  # if trial was successfull
                    successful_trials.append(d[key])
        return successful_trials

    def dict_to_list(self, d):
        '''returns a list with dict contents'''
        l = []
        for key in d.keys():
            l.append(d[key])
        return l
