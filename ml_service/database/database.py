from knowledge_processor.knowledge_manager import KnowledgeManager
from mongodb_client.mongodb_client import MongoDBClient
from socketserver import ThreadingMixIn

import random
import logging
import numpy as np
from xmlrpc.server import SimpleXMLRPCServer


logger = logging.getLogger("ml_service")


class DatabaseServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class Database():
    def __init__(self, port):
        # Database names:
        self.task_knowledge_db_name = "global_knowledge"            # knowledge of single tasks
        self.results_db_name = "global_ml_results"                  # raw result data

        self.rpc_server = None
        self.db_client = MongoDBClient()
        self.knowledge_manager = KnowledgeManager()
        self.port = port

        self.stop = False
    
    def start_server(self):
        """makes all functions available over rpc"""
        self.rpc_server = DatabaseServer(("0.0.0.0", self.port), allow_none=True, logRequests=False)
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.store_result, "store_result")
        self.rpc_server.register_function(self.get_similar_knowledge, "get_similar_knowledge")
        self.rpc_server.register_function(self.get_predicted_knowledge, "get_predicted_knowledge")
        self.rpc_server.register_function(self.process_knowledge, "process_knowledge")
        self.rpc_server.register_function(self.stop_server, "stop_server")
        self.rpc_server.register_function(self.push_trial, "push_trial")
        self.rpc_server.register_function(self.request_trials, "request_trials")
        self.rpc_server.register_function(self.push_trial_2, "push_trial_2")
        self.rpc_server.register_function(self.request_online_evaluation, "request_online_evaluation")
        self.rpc_server.register_function(self.clear_memory, "clear_memory")
        logger.debug("databse.start_server: starting rpc server with global database at port "+str(self.port))
        #self.rpc_server.serve_forever()
        self.stop = False
        while not self.stop:
            self.rpc_server.handle_request()
        logger.debug("databse: Global database rpc server has stopped")
        return True

    def store_result(self, result: dict):
        """takes whole ml data of task and saves it to database"""
        logger.debug("Database.store_result")
        if isinstance(result,dict):
            logger.debug("Database.store_result: store task result")
            task_type = result["meta"]["task_type"]
            task_id = self.db_client.write(self.results_db_name,task_type,result)
        else:
            logger.error("Database.store_result: Received result is not of type dict or list! "+str(type(result)))
            return False
        task_identity = {"task_type":result["meta"]["task_type"],
                         "tags":result["meta"]["tags"],
                         "optimum_weights":result["meta"]["cost_function"]["optimum_weights"],
                         "geometry_factor": result["meta"]["cost_function"]["geometry_factor"]}

        return task_id

    def get_predicted_knowledge(self, task_identity: dict):
        """return knowledge from single task found on database"""
        # use knowledge processor to look up/generate global knowledge:
        #knowledge = self.knowledge_manager.get_local_knowledge(task_identity,knowledge_db=self.task_knowledge_db_name,data_db=self.results_db_name)
        knowledge = self.knowledge_manager.get_predicted_knowledge(task_identity, self.task_knowledge_db_name)
        return knowledge

    def get_similar_knowledge(self, task_identity: dict, knowledge_tags: dict):
        """return knowledge from single task found on database"""
        # use knowledge processor to look up/generate global knowledge:
        knowledge = self.knowledge_manager.get_similar_knowledge(task_identity, knowledge_tags, knowledge_db=self.task_knowledge_db_name, data_db=self.results_db_name)
        return knowledge

    def process_knowledge(self, task_identity: dict):
        """process raw ml data on the database to knowledge and saves it on the database"""
        knowledge = self.knowledge_manager.get_knowledge_by_identity(self.db_client, task_identity, self.results_db_name, self.task_knowledge_db_name)
        if knowledge is False:
            logger.error("Database.process_knowledge: Cant process knowledge!")
        else:
            self.knowledge_manager.store_knowledge(self.db_client, knowledge, "global_knowledge")
        del knowledge["_id"]
        return knowledge

    def stop_server(self):
        logger.debug("database.stop_server")
        self.stop = True

    def push_trial(self, agent: str, theta: list, cost: float, keep_size: int):
        self.knowledge_manager.push_trial(agent, theta, cost, keep_size)

    def request_trials(self, n_trials: int):
        return self.knowledge_manager.request_trials(n_trials)

    def push_trial_2(self, theta, cost, task_parameter):
        self.knowledge_manager.push_trial_2(theta, cost, task_parameter)

    def request_online_evaluation(self, theta, task_parameter):
        return self.knowledge_manager.request_online_evaluation(theta, task_parameter)

    def clear_memory(self):
        self.knowledge_manager.clear_memory()


