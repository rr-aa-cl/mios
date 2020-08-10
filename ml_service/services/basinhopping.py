import logging
from scipy import optimize
from engine.engine import Trial

from services.base_service import BaseService


class BasinhoppingService(BaseService):
    def __init__(self):
        super().__init__()

    def _initialize(self):
        pass

    def _learn_task(self) -> bool:
        optimize.basinhopping()

    def trial(self, x):

        t = Trial()
        self.engine.push_trial(t)

