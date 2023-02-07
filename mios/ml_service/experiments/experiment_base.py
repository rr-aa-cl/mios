import logging
from abc import ABCMeta
from abc import abstractmethod
from threading import Thread
from task_scheduler.task_scheduler import TaskScheduler
from task_scheduler.creation_pipeline import CreationPipeline
from utils.cluster_control import *
from utils.database import *
from plotting.data_acquisition import get_multiple_experiment_data
from plotting.data_processor import DataProcessor
import numpy as np


logger = logging.getLogger("ml_service")


class Experiment(metaclass=ABCMeta):
    def __init__(self, notification_user_token: str = "", notification_api_token: str = ""):
        self.tags = []
        self.task_scheduler = TaskScheduler(notification_user_token, notification_api_token)
        self.creation_pipeline = None
        self.agents = []
        self.task_type = None

    def insert_creation_pipeline(self, pipeline: CreationPipeline):
        self.creation_pipeline = pipeline

    def start(self, tags: [], knowledge_mode: str, knowledge_type: str, global_database: str, use_cost_grid: str = None,
              optima_percentage: float = 0.01, blocking: bool = False):
        self.tags = tags
        self.task_scheduler.kb_location = global_database
        self.initialize(knowledge_mode, knowledge_type)
        if self.creation_pipeline is None:
            logger.error("No creation pipeline was provided.")

        if use_cost_grid is not None:
            cost_grid = self.get_cost_grid(use_cost_grid, optima_percentage)

        for t in self.creation_pipeline.tasks:
            t.problem_definition.tags.extend(self.tags)
            t.knowledge_tags = self.tags
            if use_cost_grid is not None:
                t.problem_definition.cost_function.cost_grid_weights = cost_grid[0, :-1]
                t.problem_definition.cost_function.cost_grid_val = cost_grid[0, -1]
                t.problem_definition.cost_function.cost_grid_weights = t.problem_definition.cost_function.cost_grid_weights.reshape(1, -1)
                t.problem_definition.cost_function.cost_grid_val = t.problem_definition.cost_function.cost_grid_val.reshape(1, -1)
                for i in range(1, cost_grid.shape[0]):
                    t.problem_definition.cost_function.add_to_cost_grid(cost_grid[i, 0], cost_grid[i, 1:-1], cost_grid[i, -1])
            self.task_scheduler.add_task(t)

        delete_local_results(self.agents, "ml_results", self.task_type, self.tags)
        delete_local_knowledge(self.agents, "local_knowledge", self.task_type, self.tags)
        delete_global_results(global_database, "global_ml_results", self.task_type, self.tags)
        delete_global_knowledge(global_database, "global_knowledge", self.task_type, self.tags)
        if blocking is False:
            thr = Thread(target=self.task_scheduler.solve_tasks)
            thr.start()
        else:
            self.task_scheduler.solve_tasks()

    def get_cost_grid(self, tag: str, percentage: float) -> np.ndarray:
        results = get_multiple_experiment_data(self.task_scheduler.kb_location, self.task_type, "ml_results",  {"meta.tags": {"$all": [tag] }})
        processor = DataProcessor()
        return processor.get_optima_by_task_identity(results, percentage)


    def stop(self):
        self.task_scheduler.stop()
        stop_ml_services(self.task_scheduler.services)

    @abstractmethod
    def initialize(self, knowledge_mode, knowledge_type):
        raise NotImplementedError
