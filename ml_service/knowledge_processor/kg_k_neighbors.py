from knowledge_processor.knowledge_generalizer_base import KnowledgeGeneralizerBase
from sklearn.neighbors import KNeighborsRegressor
import numpy as np


class KGKNeighbors(KnowledgeGeneralizerBase):
    def __init__(self):
        super().__init__()
        self.regr = KNeighborsRegressor(n_neighbors=4)

    def fit_data(self, x: np.ndarray, y: np.ndarray):
        self.regr.fit(x, y)

    def predict_data(self, x: np.ndarray):
        return self.regr.predict(x.reshape(1, -1))
