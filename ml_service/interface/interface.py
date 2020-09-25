import logging
import sys
from threading import Thread
import uuid
import time

from services.generic_optimizer import GenericOptimizerConfiguration
from services.generic_optimizer import GenericOptimizerService
from services.cmaes import *
from services.base_service import ServiceConfiguration
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.domain import Domain
from utils.udp_client import call_method

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler


logger = logging.getLogger("ml_service")


class Interface:
    """Class that provides basic controlling functions for ml_service"""

    def __init__(self):
        self.service = None
        self.learn_thread = None
        self.rpc_server = None

    def start_rpc_server(self, port: int = 8000):
        self.rpc_server = SimpleXMLRPCServer(("localhost", port), allow_none=True)
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.start_service_wrapper, "start_service")
        self.rpc_server.register_function(self.is_busy, "is_busy")
        self.rpc_server.register_function(self.wait_for_service, "wait_for_service")
        self.rpc_server.serve_forever()

    def start_service_wrapper(self, problem_definition: dict, configuration: dict, agents, knowledge: dict = None):
        service_configuration = CMAESConfiguration()
        service_configuration.from_dict(configuration)
        self.start_service(ProblemDefinition.from_dict(problem_definition), service_configuration, set(agents),
                           knowledge)

    def start_service(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                   agents: set, knowledge: dict = None) -> str:
        problem_definition.uuid = str(uuid.uuid4())
        if configuration.service_name == "cmaes":
            self.service = CMAESService()
        elif configuration.service_name == "generic":
            self.service = GenericOptimizerService()
        else:
            logger.error("Service with name " + configuration.service_name + " does not exist.")
            return "INVALID"

        self.learn_thread = Thread(target=self.learn_task, args=(problem_definition, configuration, agents, knowledge),daemon=False)
        self.learn_thread.start()
        return problem_definition.uuid

    def learn_task(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                   agents: set, knowledge:dict) -> bool:
        """strt to learn a task according to instructions"""
        logger.debug("interface.learn_task: start learning task")
        if self.service.initialize(problem_definition, configuration, agents, knowledge) is False:
            return False
        logger.debug("Gradient descent initialized ")
        result = self.service.learn_task()
        logger.debug("learning success "+str(result))
        return result

    def stop_service(self):
        """Stop the learning process, if possible save all results and stop the robot"""
        self.service.stop()

    def is_ready(self, agents) -> bool:
        if self.learn_thread is not None:
            return False
        for a in agents:
            response = call_method(a, 12002, "is_busy")
            if response["result"]["busy"] is True:
                return False

        return True

    def is_busy(self) -> bool:
        if self.learn_thread is None:
            return False
        return self.learn_thread.is_alive()

    def wait_for_service(self):
        while self.is_busy():
            time.sleep(1)

    def get_status(self) -> str:
        """returns a detailed status for debugging purposes"""
        pass

    def download_results(self):
        """returns the results of a learned task from the Database"""
        pass