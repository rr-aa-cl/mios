from services.knowledge import Knowledge
from problem_definition.problem_definition import ProblemDefinition
from definitions.cost_functions import *
from definitions.service_configs import *

class LearningConfig:
    def __init__(self, pd:ProblemDefinition = None, sc:ServiceConfiguration = None, knowledge:Knowledge = None, priority = 0):
        self.pd = pd
        self.sc = sc
        self.knowledge = knowledge
        self.priority = priority
    def to_dict(self):
        pd_dict = None
        if self.pd:
            pd_dict = self.pd.to_dict()
        sc_dict = None
        if self.sc:
            sc_dict = self.sc.to_dict()
        knowledge_dict = None
        if self.knowledge:
            knowledge_dict = self.pd.to_dict()
        return {"pd": pd_dict,"sc":sc_dict,"knowledge":knowledge_dict, "priority": self.priority}