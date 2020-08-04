class Domain:
    def __init__(self):
        self.limits = dict()
        self.vector_mapping = list()
        for p in self.limits.keys():
            self.vector_mapping.append(p)

    def normalize(self, parameters):
        pass

    def denormalize(self):
        pass
