from knowledge_processor.knowledge_processor import KnowledgeProcessor
from mongodb_client.mongodb_client import MongoDBClient

import logging
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client


logger = logging.getLogger("ml_service")

class Database():
    def __init__(self):
        # Database names:
        self.task_knowledge_db_name = "global_knowledge"            # knowledge of single tasks
        self.general_knowledge_db_name = "global_general_knowledge" # generalized knowledge of multiple tasks
        self.results_db_name = "global_ml_results"                  # raw result data

        self.rpc_server = None
        self.db_client = MongoDBClient()
        self.knowledge_processor = KnowledgeProcessor()

        self.stop = False
    
    def start_server(self, port=8001):
        """makes all functions available over rpc"""
        self.rpc_server = SimpleXMLRPCServer(("localhost", port), allow_none=True, logRequests=False)
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.store_result, "store_result")
        self.rpc_server.register_function(self.get_knowledge, "get_knowledge")
        self.rpc_server.register_function(self.process_knowledge, "process_knowledge")
        self.rpc_server.register_function(self.process_knowledge_local, "process_knowledge_local")
        self.rpc_server.register_function(self.stop_server, "stop_server")
        logger.debug("databse.start_server: starting rpc server with global database at port "+str(port))
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
        tags = result["meta"]["tags"]
        self.process_knowledge({"_id":task_id},task_type,tags)
        return task_id

    def get_knowledge(self, filter: dict, task_type: str):
        """return knowledge from single task found on database"""
        knowledge = self.db_client.read(self.task_knowledge_db_name, task_type, filter)
        if len(knowledge) >= 1:
            knowledge = knowledge[0]
        elif len(knowledge) == 0:
            logger.error("Database.get_knowledge: Cant find knowledge with filter"+str(filter))
        return knowledge

    def process_knowledge(self, filter: dict, task_type: str, knowledge_tags: dict):
        """process raw ml data on the database to knowledge and saves it on the database"""
        id = self.knowledge_processor.process_knowledge(filter,self.results_db_name, task_type, self.task_knowledge_db_name, task_type, knowledge_tags)
        if id is False:
            logger.error("Database.process_knowledge: Cant process knowledge!")
        return id

    def process_knowledge_local(self, filter: dict, task_type: str):
        """process raw ml data on the database to knowledge and return it without saving it to the database"""
        knowledge = self.knowledge_processor.process_knowledge_local(filter,self.results_db_name, task_type)
        if knowledge is False:
            logger.error("Database.process_knowledge: Cant process knowledge!")
        return knowledge

    def stop_server(self):
        logger.debug("database.stop_server")
        self.stop = True
