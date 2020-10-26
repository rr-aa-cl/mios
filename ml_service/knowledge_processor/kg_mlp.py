from knowledge_processor.knowledge_generalizer_base import KnowledgeGeneralizerBase
from sklearn.neural_network import MLPRegressor
import numpy as np


class KGMLP(KnowledgeGeneralizerBase):
    def __init__(self):
        super().__init__()
        self.regr = MLPRegressor(hidden_layer_sizes=(1, 10, 1,), activation="relu", solver="adam", max_iter=4000)

    def fit_data(self, x: np.ndarray, y: np.ndarray):
        self.regr.fit(x, y)

    def predict_data(self, x: np.ndarray):
        return self.regr.predict(x.reshape(1, -1))
