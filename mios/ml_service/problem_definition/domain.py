import logging

import numpy as np


logger = logging.getLogger("ml_service")


class Domain:
    def __init__(self, limits: dict, context_mapping: dict, x_0: dict = None, non_shareables: list = None):
        # keys: parameters (string), values: limits (tuples)
        self.limits = limits
        self.x_0 = dict()
        self.non_shareables = list()
        for p in self.limits.keys():
            self.x_0[p] = 0

        if x_0 is not None:
            for key, val in x_0.items():
                self.x_0[key] = val
        if non_shareables is not None:
            self.non_shareables = non_shareables
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
            "context_mapping": self.context_mapping,
            "x_0": self.x_0,
            "non_shareables": self.non_shareables
        }
        return domain

    @staticmethod
    def from_dict(domain_dict):
        d = Domain(domain_dict["limits"], domain_dict["context_mapping"], domain_dict["x_0"],
                   domain_dict["non_shareables"])
        return d

    def get_default_x0(self):
        x_0 = np.empty((len(self.x_0,)))
        for i in range(len(self.x_0)):
            x_0[i] = self.x_0[self.vector_mapping[i]]
        return x_0

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

    def self_check(self) -> bool:
        healthy = True
        for l in self.limits.keys():
            if l not in self.x_0:
                logger.error("Parameter " + l + " is in domain limits but not in initial values.")
                healthy = False
            if l not in self.context_mapping:
                logger.error("Parameter " + l + " is in domain limits but not in context map.")
                healthy = False

        for x in self.x_0.keys():
            if x not in self.limits:
                logger.error("Parameter " + x + " is in initial values but not in domain limits.")
                healthy = False
            if x not in self.context_mapping:
                logger.error("Parameter " + x + " is in initial values but not in context map.")
                healthy = False

        for m in self.context_mapping.keys():
            if m not in self.limits:
                logger.error("Parameter " + m + " is in context map but not in limits.")
                healthy = False
            if m not in self.x_0:
                logger.error("Parameter " + m + " is in context map but not in initial values.")
                healthy = False

        return healthy

