import numpy as np
from scipy import optimize
import logging
from services.base_service import BaseService
from services.base_service import ServiceConfiguration
from services.optimisation_dummies import Sphere


logger = logging.getLogger("ml_service")


class GenericOptimizerConfiguration(ServiceConfiguration):
    def __init__(self):
        super().__init__("generic")
        self.method = "CG"
        self.bounds = None
        self.tol = None
        self.options = {'gtol': 1e-05, 'norm': float("Inf"), 'eps': 1.4901161193847656e-08, 'maxiter': None, 'disp': False,
                        'return_all': False, 'finite_diff_rel_step': None}


class GenericOptimizerService(BaseService):
    """Gradient descent optimisation"""

    def __init__(self):
        super().__init__()

    def _initialize(self):
        logger.info("gradient_service: initialize")

    def _learn_task(self) -> bool:
        resCG = optimize.minimize(self.trial, self.problem_definition.domain.get_default_x0(), jac=False,
                                  tol=self.configuration.tol, bounds=self.configuration.bounds,
                                  method=self.configuration.method, options=self.configuration.options)
        logger.info("GradientService: Found optimum at y=" + str(resCG.fun) + " with x=" + str(resCG.x))

        return True

    def _terminate(self):
        raise NotImplementedError

    def trial(self, x: np.array):
        logger.debug("GradientService.trial(" + str(x) + ")")

        trial_uuid = self.push_trial(x)
        results = self.wait_for_result(trial_uuid)
        if results.cost_suc is None:
            results.cost_suc = 0
            logger.debug("GradientService: Trial result cost = None  --> cost = 0")
        return results.cost_suc
