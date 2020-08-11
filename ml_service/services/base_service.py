import logging
from abc import ABCMeta
from abc import abstractmethod
from threading import Thread

from engine.engine import Engine
from problem_definition.problem_definition import ProblemDefinition

logger = logging.getLogger("ml_service")


class BaseService(metaclass=ABCMeta):
    def __init__(self):

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
        if self.problem_definition.is_valid() is False:
            logger.error("Problem definition is not valid.")
            return False

        self.engine = Engine(agents)

        self._initialize()

        self.engine_thread = Thread(target=self.engine.main_loop)
        self.engine_thread.start()

    def learn_task(self) -> bool:
        result = self._learn_task()

        return result

    def update_default_context(self, x) -> dict:
        logger.debug("BaseService.update_default_context(" + str(x) + ")")
        theta = dict()
        updated_context = self.problem_definition.default_context
        for i in range(len(self.problem_definition.domain.vector_mapping)):
            theta[self.problem_definition.domain.vector_mapping[i]] = x[i]

        logger.debug("BaseService.update_default_context.theta: " + str(theta))

        for p in theta.keys():
            for mapping in self.problem_definition.domain.context_mapping[p]:
                mapping_categories = mapping.split(".")
                self.set_nested_parameter(updated_context, mapping_categories,
                                          x[self.problem_definition.domain.vector_mapping.index(p)])

        return updated_context

    def set_nested_parameter(self, dic, keys, value):
        logger.debug("BaseService.set_nested_parameter(dic: " + str(dic) + ", " + "keys: " + str(keys) + ")")
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        tmp = keys[-1].split("-")
        if len(tmp) == 1:
            dic[keys[-1]] = value
        elif len(tmp) == 2:
            p_name = tmp[0]
            p_dim = int(tmp[1])
            if p_name not in dic:
                dic[p_name] = []
            if len(dic[p_name]) < p_dim:
                dic[p_name].extend([0] * (p_dim - len(dic[p_name])))
            dic[p_name][p_dim-1] = value

    def nested_get(self, input_dict, nested_key):
        internal_dict_value = input_dict
        for k in nested_key:
            internal_dict_value = internal_dict_value.get(k, None)
            if internal_dict_value is None:
                return None
        return internal_dict_value
