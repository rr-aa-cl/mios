import logging
import numpy as np
import random
import deap
from copy import deepcopy
from deap import algorithms
from deap import base
from deap import cma
from deap import creator
from deap import tools

from engine.engine import Trial
from services.base_service import BaseService
from services.base_service import ServiceConfiguration

logger = logging.getLogger("ml_service")


class CMAESConfiguration(ServiceConfiguration):
    def __init__(self):
        super().__init__("cmaes")
        self.n_ind = 10
        self.n_gen = 10
        self.sigma_init = 0.2

    def _to_dict(self):
        config = {
            "n_ind": self.n_ind,
            "n_gen": self.n_gen,
            "sigma_init": self.sigma_init
        }
        return config

    def _from_dict(self, config_dict):
        self.n_ind = config_dict["n_ind"]
        self.n_gen = config_dict["n_gen"]
        self.sigma_init = config_dict["sigma_init"]


class CMAESService(BaseService):
    def __init__(self):
        super().__init__()

        self.success_ratio = 0

    def _initialize(self):
        deap.creator.create("FitnessMin", deap.base.Fitness, weights=(-1.0,))
        deap.creator.create("Individual", list, fitness=deap.creator.FitnessMin)
        self.toolbox = deap.base.Toolbox()
        self.engine.register_stop_condition(self._is_learned)

    def _learn_task(self) -> bool:
        self.cnt_gen = 0

        self.toolbox.register("evaluate", self.trial)
        self.toolbox.register("map", self.map)

        sigma_init = self.configuration.sigma_init
        if self.confidence:
            sigma_init = self.confidence

        # if self.centroid == None:
        self.centroid = self.problem_definition.domain.get_default_x0()
        self.strategy = deap.cma.Strategy(centroid=self.centroid,
                                          sigma=sigma_init, mu=2)
        # else:
        #     self.centroid = self.problem_definition.domain.normalize(self.centroid)
        #     sigma_init = self.configuration.sigma_init / 4
        #     logger.debug("CMAESService._initialize(): use initial centroid "+str(self.centroid))
        #     parent = deap.creator.Individual(self.centroid)
        #     parent.fitness.values = (self.knowledge["meta"]["expected_cost"],)
        #     ptarg = 1.0 / (5 + np.sqrt(self.configuration.n_ind) / 2.0)
        #     cp = ptarg * self.configuration.n_ind / (2.0 + ptarg * self.configuration.n_ind) * 0.5
        #     self.strategy = deap.cma.StrategyOnePlusLambda(parent=parent, sigma=sigma_init, lambda_=self.configuration.n_ind, cp=cp)

        self.toolbox.register("generate", self.strategy.generate, deap.creator.Individual)
        self.toolbox.register("update", self.strategy.update)

        hof = deap.tools.HallOfFame(10)

        stats = deap.tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)

        self.eaGenerateUpdate(self.toolbox, ngen=self.configuration.n_gen, stats=stats, halloffame=hof)
        self.stop()
        logger.debug("CMAESService::_learn_task.end")
        return True

    def _terminate(self):
        pass

    def _is_learned(self) -> bool:
        if self.strategy.sigma < 0.02:
            return True
        return False

    def trial(self, f, x_set):
        pass

    def map(self, f, x_set: np.ndarray):
        logger.debug("CMAESService.trial(" + str(x_set) + ")")

        trial_uuids = []

        for x in x_set:
            trial_uuids.append(self.push_trial(x))

        costs = []
        self.success_ratio = 0
        for uuid in trial_uuids:
            result = self.wait_for_result(uuid)
            if result.final_cost is None:
                logger.error("None was returned as cost, invoking stop.")
                self.stop()
                costs.append((0,))
            else:
                self.success_ratio += result.success
                costs.append((result.final_cost,))

        self.success_ratio /= float(len(trial_uuids))

        logger.debug("CMAES costs: " + str(costs))
        return costs

    def eaGenerateUpdate(self, toolbox, ngen, halloffame=None, stats=None,
                         verbose=__debug__):
        logbook = tools.Logbook()
        logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])
        self.population = None

        for gen in range(ngen):
            # Generate a new population
            self.population = toolbox.generate()
            fitnesses = toolbox.map(toolbox.evaluate, self.population)
            for ind, fit in zip(self.population, fitnesses):
                ind.fitness.values = fit

            if halloffame is not None:
                halloffame.update(self.population)

            # Update the strategy with the evaluated individuals
            toolbox.update(self.population)
            self.confidence = float(self.strategy.sigma)
            
            print("ratio: " + str(self.success_ratio))
            print("sigma:" + str(self.strategy.sigma))

            record = stats.compile(self.population) if stats is not None else {}
            logbook.record(gen=gen, nevals=len(self.population), **record)
            if verbose:
                print(logbook.stream)

            if self.keep_running is False:
                break

        return self.population, logbook
