import logging
from scipy import optimize
import numpy as np
from engine.engine import Trial
from services.base_service import BaseService

logger = logging.getLogger("ml_service")


class BasinhoppingService(BaseService):
    def __init__(self):
        super().__init__()

    def _initialize(self):
        pass

    def _learn_task(self) -> bool:
        result = optimize.basinhopping(self.trial, self.problem_definition.domain.get_default_x0(),
                                       minimizer_kwargs={"method": "BFGS"})
        logger.info("Found global optimum of y=" + str(result.fun) + " at x=" + str(result.x))
        return True

    def _terminate(self):
        pass

    def trial(self, x: np.array):
        logger.debug("BasinhoppingService.trial(" + str(x) + ")")

        t = Trial(self.update_default_context(x), self.problem_definition.reset_instructions)
        trial_uuid = self.engine.push_trial(t)

        trial = self.engine.wait_for_trial(trial_uuid, 5)
        if trial.task_result.cost_suc is None:
            trial.task_result.cost_suc = 0
        return trial.task_result.cost_suc

