from knowledge_processor.knowledge_generalizer_base import KnowledgeGeneralizerBase
from sklearn.neighbors import KNeighborsRegressor
import numpy as np


class KGKNeighbors(KnowledgeGeneralizerBase):
    def __init__(self):
        super().__init__()
        self.regr = KNeighborsRegressor(n_neighbors=5, weights="distance", )

    def fit_data(self, x: np.ndarray, y: np.ndarray):
        self.regr.fit(np.delete(x, [1, 4, 5], 1), y)

    def predict_data(self, x: np.ndarray):
        return self.regr.predict(np.delete(x.reshape(1, -1), [1, 4, 5], 1))
