import numpy as np
from scipy import optimize
import logging
from services.base_service import BaseService
from services.optimisation_dummies import Sphere
from engine.engine import Trial


logger = logging.getLogger("ml_service")

"""Different Optimisation Services are collected here"""
class GradientService(BaseService):
    """Gradient descent optimisation"""
    def __init__(self):
        super().__init__()
        self.failure_cost = None
        self.centroid_init = None
        self.iterations = 0

        #self.logger = logging.getLogger("ml_service")

    def _initialize(self):
        logger.info("gradient_service: initialize")
        self.iterations = 0
        self.cost = None
        self.target_cost = None
        #raise NotImplementedError


    def _learn_task(self) -> bool:
        #centroid = [5,5]
        resCG = optimize.minimize(self.trial,self.problem_definition.domain.get_default_x0(),jac=False,tol=self.target_cost,method='CG')
        logger.info("GradientService: Found optimum at y=" + str(resCG.fun) +" with x=" + str(resCG.x))

        return resCG["success"]


    def _terminate(self):
        raise NotImplementedError

    def trial(self, x: np.array):
        logger.debug("GradientService.trial(" + str(x) + ")")

        t = Trial(self.update_default_context(x), self.problem_definition.reset_instructions)
        trial_uuid = self.engine.push_trial(t)

        trial = self.engine.wait_for_trial(trial_uuid, 5)
        if trial.task_result.cost_suc is None:
            trial.task_result.cost_suc = 0
            logger.debug("GradientService: Trial result cost = None  --> cost = 0")
        return trial.task_result.cost_suc
