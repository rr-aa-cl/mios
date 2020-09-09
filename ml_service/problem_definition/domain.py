import numpy as np


class Domain:
    def __init__(self, limits: dict, context_mapping: dict):
        # keys: parameters (string), values: limits (tuples)
        self.limits = limits
        # shows index of parameter
        self.vector_mapping = list()
        # keys: parameters (string), values: mapped to (list of dot-separated strings, dimensions by dash)
        self.context_mapping = context_mapping
        for p in self.limits.keys():
            self.vector_mapping.append(p)

    def to_dict(self) -> dict:
        domain = {
            "limits": self.limits,
            "vector_mapping": self.vector_mapping,
            "context_mapping": self.context_mapping
        }
        return domain

    def get_default_x0(self):
        return np.ones(len(self.limits)) * 0.5

    def normalize(self, x: np.ndarray) -> np.ndarray:
        x_norm = np.zeros((len(x),))
        for i in range(len(x)):
            x_norm[i] = (x[i] - self.limits[self.vector_mapping[i]][0]) / (
                        self.limits[self.vector_mapping[i]][1] - self.limits[self.vector_mapping[i]][0])

        return x_norm

    def denormalize(self, x_norm: np.ndarray) -> np.ndarray:
        x = np.zeros((len(x_norm),))
        for i in range(len(x_norm)):
            x[i] = x_norm[i] * (self.limits[self.vector_mapping[i]][1] - self.limits[self.vector_mapping[i]][0]) + \
                   self.limits[self.vector_mapping[i]][0]

        return x
