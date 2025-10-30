from services.knowledge import Knowledge
from problem_definition.problem_definition import ProblemDefinition
from definitions.cost_functions import *
from definitions.service_configs import *
import logging

logger = logging.getLogger("collective_manager")

class LearningConfig:
    def __init__(self, pd:ProblemDefinition = None, sc:ServiceConfiguration = None, knowledge:Knowledge = None, priority = 0, name="anon",arm="left"):
        # translate inputs into classes if needed
        if type(pd) is dict:
            self.pd = ProblemDefinition.from_dict(pd)
        else:
            self.pd = pd
        if type(sc) is dict:
            service_name = sc["service_name"]
            if service_name == "cmaes":
                self.sc = CMAESConfiguration()
                self.sc.from_dict(sc)
            elif service_name == "svm":
                self.sc = SVMConfiguration()
                self.sc.from_dict(sc)
            elif service_name == "origPSP":
                self.sc = OrigPSPConfiguration()
                self.sc.from_dict(sc)
        else:
            self.sc = sc
        if type(knowledge) is dict:
            logger.debug("knowledge was dict:"+ str(knowledge))
            self.knowledge = Knowledge()
            self.knowledge.from_dict(knowledge)
        else:
            logger.debug("knowledge is not dict, but "+str(type(knowledge)))
            self.knowledge = knowledge

        self.priority = priority
        self.name = name
        self.arm = arm
        
    def to_dict(self):
        pd_dict = None
        if self.pd:
            pd_dict = self.pd.to_dict()
        sc_dict = None
        if self.sc:
            sc_dict = self.sc.to_dict()
        knowledge_dict = None
        if self.knowledge:
            knowledge_dict = self.knowledge.to_dict()
        return {"pd": pd_dict,"sc":sc_dict,"knowledge":knowledge_dict, "priority": self.priority,"experiment_name":self.name}
