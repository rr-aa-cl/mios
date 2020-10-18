import logging
from abc import ABCMeta
from abc import abstractmethod
from threading import Thread
from task_scheduler.task_scheduler import TaskScheduler
from task_scheduler.creation_pipeline import CreationPipeline
from utils.cluster_control import *
from utils.database import *


logger = logging.getLogger("ml_service")


class Experiment(metaclass=ABCMeta):
    def __init__(self):
        self.tags = []
        self.task_scheduler = TaskScheduler()
        self.creation_pipeline = None
        self.agents = []
        self.task_type = None

    def insert_creation_pipeline(self, pipeline: CreationPipeline):
        self.creation_pipeline = pipeline

    def start(self, tags: [], knowledge_mode: str, global_database: str):
        self.task_scheduler.kb_location = global_database
        self.initialize(knowledge_mode)
        if self.creation_pipeline is None:
            logger.error("No creation pipeline was provided.")

        delete_local_results(self.agents, self.task_type, self.tags)
        delete_local_knowledge(self.agents, self.task_type, self.tags)
        delete_global_results(global_database, self.task_type, self.tags)
        delete_global_knowledge(global_database, self.task_type, self.tags)

        for t in self.creation_pipeline.tasks:
            t.problem_definition.tags.extend(tags)
            self.task_scheduler.add_task(t)

        thr = Thread(target=self.task_scheduler.solve_tasks)
        thr.start()

    def stop(self):
        self.task_scheduler.stop()
        stop_ml_services(self.task_scheduler.services)

    @abstractmethod
    def initialize(self, knowledge_mode):
        raise NotImplementedError
