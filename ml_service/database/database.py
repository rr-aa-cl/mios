from knowledge_processor.knowledge_manager import KnowledgeManager
from mongodb_client.mongodb_client import MongoDBClient
from socketserver import ThreadingMixIn

import logging
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
        task_identity = {"task_type":result["meta"]["task_type"], \
                         "tags":result["meta"]["tags"], \
                         "optimum_weights":result["meta"]["cost_function"]["optimum_weights"],
                         "geometry_factor": result["meta"]["cost_function"]["geometry_factor"]}
        self.process_knowledge(task_identity)
        return task_id

    def get_predicted_knowledge(self, task_identity: dict):
        """return knowledge from single task found on database"""
        # use knowledge processor to look up/generate global knowledge:
        #knowledge = self.knowledge_manager.get_local_knowledge(task_identity,knowledge_db=self.task_knowledge_db_name,data_db=self.results_db_name)
        knowledge = self.knowledge_manager.predict_knowledge(task_identity,self.task_knowledge_db_name)
        return knowledge

    def get_similar_knowledge(self, task_identity: dict):
        """return knowledge from single task found on database"""
        # use knowledge processor to look up/generate global knowledge:
        knowledge = self.knowledge_manager.get_local_knowledge(task_identity,knowledge_db=self.task_knowledge_db_name,data_db=self.results_db_name)
        return knowledge

    def process_knowledge(self, task_identity: dict):
        """process raw ml data on the database to knowledge and saves it on the database"""
        id = self.knowledge_manager.process_knowledge(task_identity, self.results_db_name, self.task_knowledge_db_name)
        if id is False:
            logger.error("Database.process_knowledge: Cant process knowledge!")
        return id

    def stop_server(self):
        logger.debug("database.stop_server")
        self.stop = True
