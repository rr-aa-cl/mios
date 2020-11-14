import logging
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from task_scheduler.task_scheduler import Task
import copy
from abc import ABCMeta
from abc import abstractmethod


class CreationPipeline(metaclass=ABCMeta):
    def __init__(self):
        self.tasks = []

    @abstractmethod
    def create_tasks_from_template(self, template: ProblemDefinition, service_configuration: ServiceConfiguration, n_tasks, service_url, agents, knowledge_mode: str, knowledge_type: str):
        raise NotImplementedError
