import logging

from services.gradient_descent import GradientService
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.domain import Domain

class Interface:
    """Class that provides basic controlling functions for ml_service"""

    def __init__(self):
        self.logger = logging.getLogger("ml_service")
        self.G = GradientService()
        pass

    def learn_task(self, problem_definition: ProblemDefinition, agents: set) -> bool:
        """strt to learn a task according to instructions"""
        self.logger.debug("interface.learn_task: start learning task")
        
        # Problem Definition (needed here? where will it be defined?):
        #domain = Domain()
        #default_context = dict()
        #setup_instructions = list()
        #termination_instruction = list()
        #reset_instruction = list()
        #problem_definition = ProblemDefinition(domain, default_context, setup_instructions, termination_instruction, reset_instruction)

        self.G.initialize(problem_definition, agents)
        self.logger.debug("Gradient descent initialized ")
        G_learned = self.G.learn_task()
        self.logger.debug("learning success "+str(G_learned))
        return G_learned

    def stop_task(self):
        """Stop the learning process, if possible save all results and stop the robot"""
        raise NotImplementedError

    def is_busy(self) -> bool:
        """returns true if the learning process is ongoing"""
        pass

    def get_status(self) -> str:
        """returns a detailed status for debugging purposes"""
        pass

    def download_results(self):
        """returns the results of a learned task from the Database"""
        pass