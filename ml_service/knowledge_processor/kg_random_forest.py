from knowledge_processor.knowledge_generalizer_base import KnowledgeGeneralizerBase
from sklearn.ensemble import RandomForestRegressor
import numpy as np


class KGRandomForest(KnowledgeGeneralizerBase):
    def __init__(self):
        super().__init__()
        self.regr = RandomForestRegressor(max_depth=5, random_state=2)

    def fit_data(self, x: np.ndarray, y: np.ndarray):
        self.regr.fit(x, y)

    def predict_data(self, x: np.ndarray):
        return self.regr.predict(x.reshape(1, -1))
