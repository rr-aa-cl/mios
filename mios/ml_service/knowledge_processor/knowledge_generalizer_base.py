from abc import ABCMeta
from abc import abstractmethod
import numpy as np


class KnowledgeGeneralizerBase(metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def fit_data(self, x: np.ndarray, y: np.ndarray):
        raise NotImplementedError

    def predict_data(self, x: np.ndarray):
        raise NotImplementedError
