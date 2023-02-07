from knowledge_processor.knowledge_generalizer_base import KnowledgeGeneralizerBase
from sklearn.ensemble import RandomForestRegressor
import numpy as np


class KGRandomForest(KnowledgeGeneralizerBase):
    def __init__(self):
        super().__init__()
        self.regr = RandomForestRegressor(max_depth=10, random_state=2)

    def fit_data(self, x: np.ndarray, y: np.ndarray):
        self.regr.fit(np.delete(x, [1, 4, 5], 1), y)

    def predict_data(self, x: np.ndarray):
        return self.regr.predict(np.delete(x.reshape(1, -1), [1, 4, 5], 1))
