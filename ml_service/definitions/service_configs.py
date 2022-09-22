from definitions.definitions_base import *
from services.svm import SVMConfiguration
from services.cmaes import CMAESConfiguration


class SVMLearner(LearnerFactory):
    def __init__(self, n_trials: int = 130, batch_width: int = 10, n_immigrant: int = 0,  exploration_mode = True, 
                    batch_synchronisation = False, request_probability = 0.0, request_probability_decrease = False):
        super().__init__(SVMConfiguration())
        self.configuration.exploration_mode = exploration_mode
        self.configuration.n_trials = n_trials
        self.configuration.batch_width = batch_width
        self.configuration.n_immigrant = n_immigrant
        self.configuration.batch_synchronisation = batch_synchronisation
        self.configuration.request_probability = request_probability
        self.configuration.request_probability_decrease = request_probability_decrease


class CMAESLearner(LearnerFactory):
    def __init__(self, n_ind: int = 10, n_gen: int = 13, exploration_mode = True):
        super().__init__(CMAESConfiguration())
        self.configuration.exploration_mode = exploration_mode
        self.configuration.n_ind = n_ind
        self.configuration.n_gen = n_gen