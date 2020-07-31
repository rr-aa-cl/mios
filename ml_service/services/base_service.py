import logging
from abc import ABCMeta
from abc import abstractmethod
from threading import Thread

from engine.engine import Engine
from problem_definition.problem_definition import ProblemDefinition


class BaseService(metaclass=ABCMeta):
    def __init__(self):
        self.logger = logging.getLogger("ml_service")
        self.engine = None
        self.problem_definition = None
        self.engine_thread = None

    @abstractmethod
    def _initialize(self):
        raise NotImplementedError

    @abstractmethod
    def _learn_task(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _terminate(self):
        raise NotImplementedError

    def initialize(self, problem_definition: ProblemDefinition, agents: set) -> (bool, str):
        self.problem_definition = problem_definition
        self.problem_definition.is_valid()

        self.engine = Engine(agents)

        self._initialize()

        self.engine_thread = Thread(target=self.engine.main_loop)
        self.engine_thread.start()

    def learn_task(self) -> bool:
        result = self._learn_task()

        return result
