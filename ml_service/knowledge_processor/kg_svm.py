from knowledge_processor.knowledge_generalizer_base import KnowledgeGeneralizerBase
from sklearn.svm import SVR
import numpy as np


class KGSVM(KnowledgeGeneralizerBase):
    def __init__(self):
        super().__init__()
        self.svm = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=.1)

    def fit_data(self, x: np.ndarray, y: np.ndarray):
        self.svm.fit(x, y)

    def predict_data(self, x: np.ndarray):
        return self.svm.predict(x.reshape(1, -1))
