import logging
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from task_scheduler.task_scheduler import Task
from definitions import insert_cylinder_30
import copy


class CreationPipeline:
    def __init__(self):
        self.tasks = []

    def create_tasks_from_template(self, template: ProblemDefinition, service_configuration: ServiceConfiguration, n_tasks, service_url, agents, knowledge_mode: str):
        for i in range(n_tasks):
            t = Task(copy.deepcopy(template), service_configuration, agents, service_url, knowledge_mode)
            t.problem_definition.cost_function.optimum_weights[0] = float(i+1)/float(n_tasks)
            t.problem_definition.cost_function.optimum_weights[1] = 1 - t.problem_definition.cost_function.optimum_weights[0]
            self.tasks.append(t)
