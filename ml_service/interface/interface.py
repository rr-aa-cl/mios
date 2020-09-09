import logging
import sys
from threading import Thread
import uuid

from services.generic_optimizer import GenericOptimizerConfiguration
from services.generic_optimizer import GenericOptimizerService
from services.cmaes import *
from services.base_service import ServiceConfiguration
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.domain import Domain


logger = logging.getLogger("ml_service")


class Interface:
    """Class that provides basic controlling functions for ml_service"""

    def __init__(self):
        self.service = None
        self.learn_thread = None

    def start_service(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                   agents: set, knowledge:dict = None) -> str:
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

    def is_busy(self) -> bool:
        if self.learn_thread is None:
            return False
        return self.learn_thread.is_alive()


    def get_status(self) -> str:
        """returns a detailed status for debugging purposes"""
        pass

    def download_results(self):
        """returns the results of a learned task from the Database"""
        pass