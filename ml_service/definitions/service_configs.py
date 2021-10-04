from definitions.definitions_base import *
from services.svm import SVMConfiguration


class SVMLearner(LearnerFactory):
    def __init__(self, n_trials: int = 130, batch_width: int = 10, exploration_mode = False):
        super().__init__(SVMConfiguration())
        self.configuration.exploration_mode = exploration_mode
        self.configuration.n_trials = n_trials
        self.configuration.batch_width = batch_width