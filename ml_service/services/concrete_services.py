from scipy import optimize
import logging
from services.base_service import BaseService
from services.optimisation_dummies import Sphere

"""Different Optimisation Services are collected here"""

class GradientService(BaseService):
    """Gradient descent optimisation"""
    def __init__(self):
        super().__init__()
        self.failure_cost = None
        self.centroid_init = None
        self.iterations = 0

        self.logger = logging.getLogger("ml_service")

    def _initialize(self):
        logging.info("gradient_service: _initialize (nothing to initialize, problem_definition/domain not implemented...)")
        self.iterations = 0
        self.cost = None
        self.target_cost = None
        #raise NotImplementedError


    def _learn_task(self) -> bool:
        centroid = [5,5]
        resCG = optimize.minimize(self.run_trial,centroid,jac=False,tol=self.target_cost,method='CG')
        print(resCG)

        return resCG["success"]


    def _terminate(self):
        raise NotImplementedError

    def run_trial(self, input):
        #ToDo: connect to LoadBalancer
        #ToDo: connect to KnowledgeProcessor
        self.iterations += 1
        result = Sphere(input)
        self.cost = result["result"]["cost_suc"]
        #result["result"]=1
        #result["cost_suc"]=res
        #result["cost_err"]=0
        return result["result"]["cost_suc"]