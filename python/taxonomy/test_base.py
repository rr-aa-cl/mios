import abc
from abc import ABC
import os


class BaseTest(ABC):

    def __init__(self, robot: str, skill_class: str):
        self.db_host = "collective-control-001"
        self.db = "taxonomy"
        self.robot = robot
        self.path_to_default_context = os.getcwd() + "/default_contexts/"
        self.skill_class = skill_class
        self.default_context = dict()
        self.reset_default_contexts = dict()
        self.record_performance = False

    def initialize(self, default_context: dict, reset_default_contexts: dict, record_performance: bool = True):
        self.default_context = default_context
        self.reset_default_contexts = reset_default_contexts
        self.record_performance = record_performance

    @abc.abstractmethod
    def run(self, args: dict, result_uuid: str = None, result_trial: int = None):
        raise NotImplementedError

    @abc.abstractmethod
    def reset(self, args: dict):
        raise NotImplementedError

    @abc.abstractmethod
    def teach(self, args: dict):
        raise NotImplementedError


def start_experiment(skill_test: BaseTest, run_args: dict, reset_args: dict, n_iter: int, result_id: str = None,
                     result_trial: int = None):
    for i in range(n_iter):
        skill_test.run(run_args, result_id, result_trial)
        skill_test.reset(reset_args)
