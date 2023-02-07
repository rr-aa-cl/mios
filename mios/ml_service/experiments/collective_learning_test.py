from task_scheduler.creation_pipeline import CreationPipeline
from services.cmaes import CMAESConfiguration
from services.svm import SVMConfiguration
from task_scheduler.task_scheduler import TaskScheduler
from task_scheduler.task_scheduler import Task
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from definitions.benchmark_definitions import mios_ml_benchmark
from experiments.experiment_base import Experiment
from utils.udp_client import *
import copy
import random


def rastrigin_a(a: float):
    pd = mios_ml_benchmark(a)
    pd.tags = ["rastrigin_" + str(int(a))]
    pd.cost_function.geometry_factor = a
    pd.cost_function.max_cost[2] = pow(a + 5.12, 2) * 6
    return pd


class TestCreationPipeline(CreationPipeline):
    def __init__(self):
        super().__init__()

    def create_tasks_from_template(self, template: ProblemDefinition, service_configuration: ServiceConfiguration, n_tasks, service_url, agents, knowledge_mode: str, knowledge_type: str = "similar"):
        for i in range(n_tasks):
            t = Task(copy.deepcopy(template), service_configuration, agents, service_url, knowledge_mode, knowledge_type)
            t.problem_definition.cost_function.optimum_weights[0] = 0
            t.problem_definition.cost_function.optimum_weights[1] = float(i) / float(n_tasks)
            t.problem_definition.cost_function.optimum_weights[2] = 1 - \
                                                                    t.problem_definition.cost_function.optimum_weights[
                                                                        1]
            self.tasks.append(t)

        random.shuffle(self.tasks)


class CollectiveLearningBase(Experiment):
    def initialize(self, knowledge_mode: str, knowledge_type: str = "prediction"):
        config = CMAESConfiguration()
        config.exploration_mode = False
        config.n_gen = 30
        config.n_ind = 10

        config.n_trials = 200
        config.exploration_mode = False

        self.agents = ["collective-panda-007.local", "collective-panda-001.local", "collective-panda-008.local",
                       "collective-panda-002.local", "collective-panda-009.local"]
        self.task_type = "benchmark_rastrigin"

        c = TestCreationPipeline()
        n_tasks = 20
        c.create_tasks_from_template(rastrigin_a(1), config, n_tasks, "collective-panda-007.local",
                                     ["collective-panda-007"], knowledge_mode, knowledge_type)
        c.create_tasks_from_template(rastrigin_a(2), config, n_tasks, "collective-panda-001.local",
                                     ["collective-panda-001"], knowledge_mode, knowledge_type)
        c.create_tasks_from_template(rastrigin_a(3), config, n_tasks, "collective-panda-008.local",
                                     ["collective-panda-008"], knowledge_mode, knowledge_type)
        c.create_tasks_from_template(rastrigin_a(4), config, n_tasks, "collective-panda-002.local",
                                     ["collective-panda-002"], knowledge_mode, knowledge_type)
        c.create_tasks_from_template(rastrigin_a(5), config, n_tasks, "collective-panda-009.local",
                                     ["collective-panda-009"], knowledge_mode, knowledge_type)

        self.insert_creation_pipeline(c)
