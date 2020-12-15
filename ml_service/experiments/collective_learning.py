from task_scheduler.task_scheduler import Task
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from task_scheduler.creation_pipeline import CreationPipeline
from services.cmaes import CMAESConfiguration
from definitions.insertion_definitions import insert_key
from definitions.insertion_definitions import insert_cylinder
from utils.udp_client import call_method
from experiments.experiment_base import Experiment
import copy
import random


class TestCreationPipeline(CreationPipeline):
    def __init__(self):
        super().__init__()

    def create_tasks_from_template(self, template: ProblemDefinition, service_configuration: ServiceConfiguration,
                                   n_tasks, service_url, agents, knowledge_mode: str, knowledge_type: str = "similar"):
        for i in range(n_tasks):
            t = Task(copy.deepcopy(template), service_configuration, agents, service_url, knowledge_mode, knowledge_type)
            t.problem_definition.cost_function.optimum_weights[0] = float(i + 1) / float(n_tasks)
            t.problem_definition.cost_function.optimum_weights[2] = 1 - \
                                                                    t.problem_definition.cost_function.optimum_weights[
                                                                        0]
            self.tasks.append(t)

        random.shuffle(self.tasks)


class CollectiveLearningBase(Experiment):
    def initialize(self, knowledge_mode: str, knowledge_type: str = "similar"):
        config = CMAESConfiguration()
        config.n_gen = 10
        config.n_ind = 13
        config.exploration_mode = True

        call_method("collective-panda-001.local", 12002, "set_grasped_object", {"object": "cylinder_40"})
        call_method("collective-panda-002.local", 12002, "set_grasped_object", {"object": "key_hatch"})
        call_method("collective-panda-007.local", 12002, "set_grasped_object", {"object": "cylinder_10"})
        call_method("collective-panda-008.local", 12002, "set_grasped_object", {"object": "cylinder_60"})
        call_method("collective-panda-009.local", 12002, "set_grasped_object", {"object": "key_pad"})

        self.agents = ["collective-panda-007.local", "collective-panda-001.local", "collective-panda-008.local",
                       "collective-panda-002.local", "collective-panda-009.local"]
        self.task_type = "insert_object"

        c = TestCreationPipeline()
        n_tasks = 10
        c.create_tasks_from_template(insert_cylinder(10, 0.5), config, n_tasks, "collective-panda-007.local",
                                     ["collective-panda-007"], knowledge_mode, knowledge_type)
        c.create_tasks_from_template(insert_cylinder(40, 0.8), config, n_tasks, "collective-panda-001.local",
                                     ["collective-panda-001"], knowledge_mode, knowledge_type)
        c.create_tasks_from_template(insert_cylinder(60, 1), config, n_tasks, "collective-panda-008.local",
                                     ["collective-panda-008"], knowledge_mode, knowledge_type)
        c.create_tasks_from_template(insert_key("hatch", 0.3), config, n_tasks, "collective-panda-002.local",
                                     ["collective-panda-002"], knowledge_mode, knowledge_type)
        c.create_tasks_from_template(insert_key("pad", 0.1), config, n_tasks, "collective-panda-009.local",
                                     ["collective-panda-009"], knowledge_mode, knowledge_type)

        self.insert_creation_pipeline(c)
