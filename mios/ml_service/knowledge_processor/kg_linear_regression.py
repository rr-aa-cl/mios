from knowledge_processor.knowledge_generalizer_base import KnowledgeGeneralizerBase
from sklearn import linear_model
import numpy as np


class KGLinearRegressor(KnowledgeGeneralizerBase):
    def __init__(self):
        super().__init__()
        self.linear_regressor = linear_model.LinearRegression()

    def fit_data(self, x: np.ndarray, y: np.ndarray):
        self.linear_regressor.fit(x, y)

    def predict_data(self, x: np.ndarray):
        return self.linear_regressor.predict(x.reshape(1, -1))