import logging
import numpy as np
import random
import deap
import time
from deap import base
from deap import cma
from deap import creator
from deap import tools
from xmlrpc.client import ServerProxy

from services.base_service import BaseService
from services.base_service import ServiceConfiguration

logger = logging.getLogger("ml_service")


class CMAESConfiguration(ServiceConfiguration):
    def __init__(self):
        super().__init__("cmaes")
        self.n_ind = 10
        self.n_gen = 10
        self.sigma_init = 0.2
        self.n_immigrant = 0

    def _to_dict(self):
        config = {
            "n_ind": self.n_ind,
            "n_gen": self.n_gen,
            "sigma_init": self.sigma_init,
            "n_immigrant": self.n_immigrant
        }
        return config

    def _from_dict(self, config_dict):
        self.n_ind = config_dict["n_ind"]
        self.n_gen = config_dict["n_gen"]
        self.sigma_init = config_dict["sigma_init"]
        self.n_immigrant = config_dict["n_immigrant"]


class CMAESService(BaseService):
    def __init__(self, mios_port=12000, mongo_port=27017):
        super().__init__(mios_port,mongo_port)

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

        if self.centroid is None:
            self.centroid = self.problem_definition.domain.get_default_x0()

        print("CMAES: " + str(self.centroid))
        print(self.problem_definition.domain.vector_mapping)
        self.strategy = deap.cma.Strategy(centroid=self.centroid, sigma=sigma_init, lambda_=self.configuration.n_ind)
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
        # logger.debug("CMAESService.trial(" + str(x_set) + ")")

        trial_uuids = dict()

        for x in x_set:
            uuid = self.push_trial(x)
            trial_uuids[uuid] = x

        costs = []
        self.success_ratio = 0
        if self.knowledge_source is None:
            kb = None
        else:
            kb = ServerProxy("http://" + self.knowledge_source["kb_location"] + ":8001")
        for uuid in trial_uuids.keys():
            result = self.wait_for_result(uuid)
            if result.q_metric.final_cost is None:
                logger.error("None was returned as cost for trial " + uuid + ", invoking stop.")
                self.stop()
                costs.append((0,))
            else:
                self.success_ratio += result.q_metric.success
                costs.append((result.q_metric.final_cost,))
            theta = []
            for i in range(len(trial_uuids[uuid])):
                theta.append(float(trial_uuids[uuid][i]))
            if kb is not None:
                pass
                #kb.push_trial(self.host_name, theta, float(result.q_metric.final_cost), self.configuration.n_ind)
                # kb.push_trial_2(theta, float(result.q_metric.final_cost), self.problem_definition.cost_function.geometry_factor)
        self.success_ratio /= float(len(trial_uuids.keys()))

        logger.debug("CMAES costs: " + str(costs))
        return costs

    def eaGenerateUpdate(self, toolbox, ngen, halloffame=None, stats=None,
                         verbose=__debug__):
        logbook = tools.Logbook()
        logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])
        self.population = None

        if self.knowledge_source is None:
            kb = None
        else:
            kb = ServerProxy("http://" + self.knowledge_source["kb_location"] + ":8001")

        for gen in range(ngen):
            # Generate a new population
            self.population = toolbox.generate()
            # random.shuffle(self.population)
            if kb is not None:
                separated_pop = self.population[len(self.population) - self.configuration.n_immigrant:]
                self.population = self.population[:len(self.population) - self.configuration.n_immigrant]
            fitnesses = toolbox.map(toolbox.evaluate, self.population)
            # if kb is not None:
            #     theta = []
            #     for i in range(self.configuration.n_immigrant):
            #         theta.append([])
            #         for j in range(len(separated_pop[i])):
            #             theta[i].append(float(separated_pop[i][j]))
            #     while True:
            #         cost = kb.request_online_evaluation(theta, self.problem_definition.cost_function.geometry_factor)
            #         if cost is not False:
            #             for i in range(self.configuration.n_immigrant):
            #                 fitnesses.append((cost[i],))
            #             self.population.extend(separated_pop)
            #             break
            #         else:
            #             time.sleep(1)
            #             continue
                # while True:
                #     new_population = kb.request_trials(self.configuration.n_immigrant)
                #     if new_population is False:
                #         print("Not enought yet")
                #         time.sleep(1)
                #         continue
                #     else:
                #         break
                # for i in new_population:
                #     self.population.append(deap.creator.Individual(i[0]))
                #     fitnesses.append((i[1],))
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
