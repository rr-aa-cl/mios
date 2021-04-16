import logging
import numpy as np
import copy
import time
import random
from mongodb_client.mongodb_client import MongoDBClient
from knowledge_processor.knowledge_processor_v2 import KnowledgeProcessor
from knowledge_processor.kg_random_forest import KGRandomForest
from knowledge_processor.kg_k_neighbors import KGKNeighbors
from knowledge_processor.knowledge_generalizer_base import KnowledgeGeneralizerBase
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from threading import Lock, Thread
from sklearn.svm import SVR
import sklearn.exceptions
from enum import Enum

logger = logging.getLogger("ml_service")


class KnowledgeManager:
    def __init__(self, host='localhost', port=27017):
        self.DBclient = MongoDBClient(host, port)
        self.data_db = "ml_results"
        self.knowledge_db = "local_knowledge"
        self.predictor = None
        self.validation_per = 0.2
        self.n_retrain = 10  # how many times the generalizer is retrained before prediction
        self.data_storage = dict()
        self.k_neighbors = KNeighborsRegressor(n_neighbors=6)
        self.mlp1 = MLPRegressor(hidden_layer_sizes=(14,), max_iter=400)
        self.mlp2 = MLPRegressor(hidden_layer_sizes=(14,), max_iter=400)
        self.svr = SVR()
        self.lock_mlp1 = Lock()
        self.lock_mlp2 = Lock()

        self.training_mlp1 = False
        self.training_mlp2 = False
        self.last_trained = "none"
        self.first_fit = False

        self.trial_data_x = []
        self.trial_data_y = []

    def collect_data(self, db_client, task_identifier, data_db: str = "ml_results") -> list:
        if "identity" in task_identifier:
            result_filter = {"meta.tags": task_identifier["tags"],
                             "meta.identity": task_identifier["identity"],
                             "meta.task_type": task_identifier["task_type"]}
        else:
            result_filter = {"meta.tags": task_identifier["tags"],
                             "meta.task_type": task_identifier["task_type"]}

        doc = db_client.read(data_db, task_identifier["task_type"], result_filter)
        if doc is None or len(doc) == 0:
            logger.error("Could not find any results for filter " + str(
                result_filter) + " on database " + data_db + " in collection " + task_identifier["task_type"] + ".")
            return []
        return doc

    def collect_knowledge(self, client: MongoDBClient, db: str, skill_class: str, knowledge_identifier: dict) -> list:
        doc = client.read(db, skill_class, knowledge_identifier)
        if doc is None or len(doc) == 0:
            logger.error("Could not find any results for filter " + str(
                knowledge_identifier) + " on database " + db + " in collection " + skill_class + ".")
            return []
        return doc

    def store_knowledge(self, db_client: MongoDBClient, knowledge: dict, scope: list, knowledge_db="local_knowledge") -> str or None:
        if knowledge is None:
            return None

        if "tags" in knowledge["meta"]:
            del knowledge["meta"]["tags"]

        knowledge["meta"]["scope"] = scope

        knowledge_filter = {"meta.scope": scope,
                            "meta.task_type": knowledge["meta"]["task_type"],
                            "meta.identity": knowledge["meta"]["identity"]}
        available_knowledge = db_client.read(knowledge_db, knowledge["meta"]["task_type"], knowledge_filter)
        if len(available_knowledge) == 0:
            logger.debug("KnowledgeManager::store_knowledge: create new knowledge entry")
            return db_client.write(knowledge_db, knowledge["meta"]["task_type"], knowledge)
        elif len(available_knowledge) == 1:
            logger.debug(
                "KnowledgeManager::store_knowledge: update knowledge entry for task identity on database " + str(
                    knowledge_db))
            id = available_knowledge[0]["_id"]
            knowledge["_id"] = id
            db_client.remove(knowledge_db, knowledge["meta"]["task_type"], {"_id": id})
            db_client.write(knowledge_db, knowledge["meta"]["task_type"], knowledge)
            return available_knowledge[0]["_id"]
        else:
            logger.error(
                "KnowledgeManager::store_knowledge: Multiple knowledge entries found! Cannot decide which one to update")
            return None

    def get_knowledge_by_identity(self, db_client, task_identifier: dict, data_db: str = "ml_results",
                                  knowledge_db: str = "local_knowledge") -> str or None:
        '''process raw data from trials to knowledge; working from and on the database'''
        # allocate all ml_data with same task identity:
        doc = self.collect_data(db_client, task_identifier, data_db)
        if not doc:
            return None
        # save knowledge source
        uuids = []
        tags = set()
        for d in doc:
            uuids.append(d["meta"]["uuid"])

        successful_trials, vector_mapping, mean_optimum_weights, confidence = self.get_successful_trials(doc)
        # process knowledge:
        knowledge_processor = KnowledgeProcessor(vector_mapping, task_identifier, mean_optimum_weights, confidence)
        knowledge = knowledge_processor.process_knowledge(successful_trials)

        if not knowledge:
            logger.error("KnowledgeManager.process_knowledge: Knowledge cant be processed!")
            return None

        knowledge["meta"]["knowledge_source"] = uuids
        knowledge["meta"]["prediction"] = False

        return knowledge

    def get_knowledge_by_filter(self, db_client: MongoDBClient, data_db: str, col: str, filter: dict):
        doc = db_client.read(data_db, col, filter)
        if not doc:
            logger.error("Cannot find data for filter " + str(filter) + " at " + str(data_db) + "." + str(col))
            return None

        task_identity = {
            "identity": doc[0]["meta"]["identity"],
            "task_type": doc[0]["meta"]["task_type"],
            "tags": doc[0]["meta"]["tags"]
        }

        successful_trials, vector_mapping, mean_optimum_weights, confidence = self.get_successful_trials(doc)
        self.knowledge_processor = KnowledgeProcessor(vector_mapping, task_identity, mean_optimum_weights, confidence)
        knowledge = self.knowledge_processor.process_knowledge(successful_trials)
        return knowledge

    def process_knowledge_local(self, db_client, task_identity: dict, data_db: str = "ml_results") -> str("_id"):
        '''process raw data from trials to knowledge; working from and on the database'''
        # allocate all ml_data with same task identity:
        doc = self.collect_data(db_client, task_identity, data_db)
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
            if not doc["meta"].get("identity", False):
                logger.error("KnowledgeManager: found invalid knowledge (no key \"identity\" in meta)")
                continue
            training_data_x.append(np.asarray(doc["meta"]["identity"]))
            training_data_y.append(np.array(self.dict_to_list(doc["parameters"])))
        if len(training_data_x) < 1 or len(training_data_y) < 1:
            logger.error(
                "KnowledgeManager.predict_knowledge: Training or Validation data is too small (smaller than 1)")
            return False
        return np.array(training_data_x), np.array(training_data_y)

    def get_cost_from_data(self, docs):
        cost_data = []
        for doc in docs:
            if not doc["meta"].get("identity", False):
                logger.error("KnowledgeManager: found invalid knowledge (no key \"identity\" in meta)")
                continue
            cost_data.append(np.array(doc["meta"]["expected_cost"]))
        if len(cost_data) < 1:
            logger.error(
                "KnowledgeManager.predict_knowledge: Training or Validation data is too small (smaller than 1)")
            return False
        return np.array(cost_data)

    def get_predictor(self):
        if self.predictor is not None:
            return self.predictor
        else:
            return KGKNeighbors()

    def get_predicted_knowledge(self, skill_class: str, scope: list, identity: list, knowledge_db: str = "local_knowledge",
                                predictor: KnowledgeGeneralizerBase = None):
        '''trains and uses model to predict knolwedge'''
        # search for all tasks of same tasktype

        knowledge_filter = {
            "meta.scope": scope,
            "meta.task_type": skill_class
        }

        doc = self.collect_knowledge(self.DBclient, knowledge_db, skill_class, knowledge_filter)

        if not doc:
            logger.error("KnowledgeManager: Cannot predict for identity " + str(identity) + ". No knowledge on " + str(
                knowledge_db) + " for skill class " + skill_class + " and scope " + str(scope) + ".")
            return False
        # check if knowledge fits together:
        vector_mapping = doc[0]["parameters"].keys()
        for d in doc:
            if vector_mapping != d["parameters"].keys():
                logger.error(
                    "KnowledgeManager.predict_knowledge: found knowledge doesnt fit together: different vector mappings!")
                return False
        if len(doc) * (1 - self.validation_per) < 5:  # if no predictions can be made: use similar knowledge
            logger.error("KnowledgeManager: Cannot predict for identity " + str(identity) + ". Not enough knowledge on " + str(
                knowledge_db) + " for skill class " + skill_class + " and scope " + str(scope) + ".")
            return False

        # get best predictor:
        if predictor is None:
            predictor = self.get_predictor()

        # retrain the knowledge generalizer and take the best one
        best_predictor = predictor
        best_error = float("inf")

        for i in range(0, int(max(1, self.n_retrain))):
            training_set = copy.deepcopy(doc)

            # divide into training-data and validation-data
            validation_size = int(len(training_set) * self.validation_per)
            if validation_size < 1 and len(training_set) > 1:
                validation_size = 1
            validation_set = []
            for i in range(0, validation_size):
                random_pic = random.randint(0, len(training_set) - 1)
                validation_set.append(training_set.pop(random_pic))

            # get learning data
            training_data = self.get_learning_data(training_set)
            validation_data = self.get_learning_data(validation_set)
            if not (training_data and validation_data):  # sth went wrong, sets too small
                logger.debug("KnowledgeManager.predict_knowledge: Error in training or validation set")
                return False

            # standardize learning data
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
                best_error = float(error_in_context)
        predictor = best_predictor

        # predict
        predict_x = np.asarray(identity)
        print("predict_x: " + str(predict_x))
        predict_x_normalized = (predict_x - mean_data_x) / std_deviation_data_x
        print("mean_data_x: " + str(mean_data_x))
        print("std_deviation_data_x: " + str(std_deviation_data_x))
        print("predict_x_normalized: " + str(predict_x_normalized))
        prediction_normalized = predictor.predict_data(predict_x_normalized)[0]
        prediction = (prediction_normalized * std_deviation_data_y) + mean_data_y

        # predict expected cost
        predictor.fit_data(training_data_x_normalized, self.get_cost_from_data(training_set))
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
        meta["prediction_error"] = best_error
        # confidence gives no good results when predicting
        # meta["confidence"] = float(best_error / np.sqrt(len(training_data_x_normalized)))  # divided by root of n_parameters because max error is root(n_parameters)
        meta["identity"] = identity
        meta["task_type"] = skill_class
        meta["scope"] = scope
        meta["time"] = time.ctime()
        meta["prediction"] = True

        knowledge = {"parameters": parameter_dict,
                     "meta": meta}

        return knowledge

    def get_similar_knowledge(self, task_identifier: dict, scope: dict, knowledge_db: str = "local_knowledge",
                              data_db: str = "ml_results"):
        '''searches for most similar knowledge / creates knowledge from similar results'''
        collection = task_identifier["task_type"]
        identity = task_identifier["identity"]

        # search knowledge from the same knowledge_pool (other tasks)
        knowledge_filter = {"meta.scope": scope,
                            "meta.task_type": task_identifier["task_type"]
                            }

        docs = self.DBclient.read(knowledge_db, collection, knowledge_filter)
        if len(docs) >= 1:
            logger.debug("knowledge_processor.get_similar_knowledge(): found knowledge on task identity" + str(
                task_identifier) + " at " + str(knowledge_db) + "." + str(collection))
            # take most similar knowledge according to cost function ("optimum_weights"):
            return self.get_most_similar_task(docs, identity)
        logger.debug("knowledge_manager.get_similar_knowledge(): can\'t find knowledge for " +
                     str(task_identifier) + " under scope " + str(scope) + " at " + str(collection))

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
            cofindence = None
            if "final_results" in doc:
                confidence = doc["final_results"].get("confidence")

        for m in metainfo:
            if m["domain"]["vector_mapping"] != metainfo[0]["domain"]["vector_mapping"]:
                logger.error("knowledge_processor: got trials from different domains. Cant process them together")
        vector_mapping = metainfo[0]["domain"]["vector_mapping"]
        return successful_trials, vector_mapping, optimum_weights, confidence

    def get_most_similar_task(self, tasks, identity: np.ndarray):
        '''find most similar task in a list of tasks according to identity'''
        # normalize weights:

        most_similar_task = tasks[0]
        smallest_dist = float('inf')
        for task in tasks:
            if "cost_function" in task["meta"].keys():
                temp_identity = np.asarray(task["meta"]["identity"])
            else:
                try:
                    temp_identity = np.asarray(task["meta"]["identity"])
                except KeyError:
                    logger.debug(
                        "knowledge_processor.get_most_similar_task: skipping faulty task format (cant find optimum_weights in task)")
                    continue

            # use euclidean distance as similarity measure:  sqrt(sum( (a-b)**2 ))
            dist = np.linalg.norm(identity - temp_identity)

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

    def push_trial(self, agent: str, theta: list, cost: float, keep_size: int):
        if agent not in self.data_storage:
            self.data_storage[agent] = []
        if len(self.data_storage[agent]) >= keep_size:
            self.data_storage[agent].pop(0)
        self.data_storage[agent].append((theta, cost))

    def request_trials(self, n_trials: int):
        n_available = 0
        n_per_agent = int(np.floor(n_trials / len(self.data_storage)))
        for a in self.data_storage.keys():
            n_available += len(self.data_storage[a])
            if len(self.data_storage[a]) < n_per_agent:
                return False

        if n_available < n_trials:
            logger.error("Number of requested trials is larger than number of available trials.")
            return False


        trials = []
        n_rest = n_trials % len(self.data_storage)
        cnt_rest = 0
        for a in self.data_storage.keys():
            if cnt_rest < n_rest:
                mod_rest = 1
            else:
                mod_rest = 0
            cnt_rest += 1
            trials_per_agent = self.data_storage[a].copy()
            random.shuffle(trials_per_agent)
            trials_per_agent = trials_per_agent[:n_per_agent + mod_rest]
            for t in trials_per_agent:
                trials.append(t)

        return trials

    def push_trial_2(self, theta: list, cost: float, task_parameter: float):
        theta.append(task_parameter)
        self.trial_data_x.append(theta)
        self.trial_data_y.append(cost)
        x = np.asarray(self.trial_data_x).reshape(-1, len(theta))
        y = np.asarray(self.trial_data_y).reshape(-1, 1)
        y = np.ravel(y)

        try:
            if self.last_trained == "none" and self.training_mlp1 is True:
                self.svr.fit(x, y)
                self.first_fit = True
            if self.last_trained == "none" and self.training_mlp1 is False:
                t = Thread(target=self.train_mlp1, args=(x, y))
                t.start()
            if self.last_trained == "mlp1" and self.training_mlp1 is False:
                t = Thread(target=self.train_mlp2, args=(x, y))
                t.start()
            if self.last_trained == "mlp2" and self.training_mlp2 is False:
                t = Thread(target=self.train_mlp1, args=(x, y))
                t.start()

        except IndexError as e:
            print("IndexError: " + str(e))
            print(x.shape)
            print(y.shape)

    def request_online_evaluation(self, theta: list, task_parameter: float):
        cost = []
        for t in theta:
            t.append(task_parameter)
            x = np.asarray(t).reshape(1, -1)
            try:
                if self.last_trained == "none" and self.first_fit is True:
                    cost.append(float(self.svr.predict(x)))
                elif self.last_trained == "mlp2" and self.training_mlp2 is False:
                    cost.append(float(self.mlp2.predict(x)))
                elif self.last_trained == "mlp1" and self.training_mlp1 is False:
                    cost.append(float(self.mlp1.predict(x)))
                else:
                    return False
            except sklearn.exceptions.NotFittedError as e:
                print(e)
                return False

        return cost

    def clear_memory(self):
        self.trial_data_x.clear()
        self.trial_data_y.clear()
        self.data_storage.clear()

    def train_mlp1(self, x, y):
        if self.lock_mlp1.acquire(False) is False:
            return
        self.training_mlp1 = True
        try:
            self.mlp1.fit(x, y)
            self.last_trained = "mlp1"
        except IndexError as e:
            print(e)
        finally:
            self.training_mlp1 = False
            self.lock_mlp1.release()

    def train_mlp2(self, x, y):
        if self.lock_mlp2.acquire(False) is False:
            return
        self.training_mlp2 = True
        try:
            self.mlp2.fit(x, y)
            self.last_trained = "mlp2"
        except IndexError as e:
            print(e)
        finally:
            self.training_mlp2 = False
            self.lock_mlp2.release()
