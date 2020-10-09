import logging
from abc import ABCMeta
from abc import abstractmethod
from threading import Thread
from xmlrpc.client import ServerProxy
import socket

from engine.engine import Engine
from engine.engine import Trial
from engine.engine import TaskResult
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.problem_definition import Domain
from knowledge_processor.knowledge_processor import KnowledgeProcessor
from utils.exception import *

logger = logging.getLogger("ml_service")


class ServiceConfiguration(metaclass=ABCMeta):
    def __init__(self, service_name: str = "none"):
        self.service_name = service_name

    @abstractmethod
    def to_dict(self):
        raise NotImplementedError

    @abstractmethod
    def from_dict(self, config_dict):
        raise NotImplementedError


class BaseService(metaclass=ABCMeta):
    def __init__(self):

        self.engine = None
        self.problem_definition = ProblemDefinition("NullTask", Domain(dict(), dict()), dict(), [], [], [], None)
        self.knowledge_processor = KnowledgeProcessor()
        self.engine_thread = None
        self.configuration = None
        self.keep_running = False
        self.centroid = None
        self.result = False
        self.database_results_id = None
        self.knowledge_source = 'none'

        # 15s timeout for xmlrpc clinet:
        socket.setdefaulttimeout(15)


    @abstractmethod
    def _initialize(self):
        raise NotImplementedError

    @abstractmethod
    def _learn_task(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _terminate(self):
        raise NotImplementedError

    def initialize(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                   agents: set, knowledge_source: dict = None) -> (bool, str):
        self.problem_definition = problem_definition
        self.configuration = configuration
        self.knowledge_source = knowledge_source
        #task_identity used for searching similar tasks:
        self.task_identity = {"tags":problem_definition.tags,"task_type":problem_definition.task_type,"optimum_weights":problem_definition.cost_function.optimum_weights}

        if self.problem_definition.is_valid() is False:
            logger.error("Problem definition is not valid.")
            return False

        if knowledge_source is not None:
            if knowledge_source["mode"] == 'none':
                self.centroid = None
            elif knowledge_source["mode"] == 'local':
                logger.debug("base_service.initialize(): get local knowlege")
                knowledge = self.knowledge_processor.get_local_knowledge(self.problem_definition.get_task_identity())
                if knowledge:
                    self.centroid = []
                    for key in knowledge["parameters"]:
                        self.centroid.append(knowledge["parameters"][key])   
                    logger.debug("base_service.initialize(): Use local knowledge "+str(self.centroid))
            elif knowledge_source["mode"] == 'global':
                logger.debug("base_service.initialize(): get global knowlege")
                knowledge = False
                with ServerProxy(knowledge_source["kb_location"]) as kb:
                    try:
                        knowledge = kb.get_knowledge(self.problem_definition.get_task_identity())
                    except socket.timeout:
                        logger.error("base_service: global Database is not reachable!")

                if knowledge:
                    self.centroid = []
                    for key in knowledge["parameters"]:
                        self.centroid.append(knowledge["parameters"][key])
                    logger.debug("base_service.initialize(): Use global knowledge "+str(self.centroid))

        self.engine = Engine(agents)
        self.database_results_id = self.engine.initialize(self.problem_definition)

        self._initialize()

        self.engine_thread = Thread(target=self.engine.main_loop)
        self.engine_thread.start()

    def learn_task(self) -> bool:
        self.keep_running = True
        try:
            result = self._learn_task()
        except StopService:
            result = False
        self.keep_running = False
        self.result = result
        # update knowledge bases:
        self.knowledge_processor.process_knowledge(self.problem_definition.get_task_identity())  # process knowledge and stores it to local db
        if self.knowledge_source is not None:
            if self.knowledge_source["mode"] == "global":
                ml_data = self.knowledge_processor.get_ml_results({"_id":self.database_results_id}, self.problem_definition.task_type)
                if len(ml_data) == 1:
                    logger.debug("base_service.learn_task: store ml_results to global database at "+str(self.knowledge_source["kb_location"]))
                    with ServerProxy(self.knowledge_source["kb_location"]) as kb:
                        try:
                            kb.store_result(ml_data[0])
                        except socket.timeout:
                            logger.error("base_service: global Database is not reachable!")
                else:
                    logger.error("base_service.learn_task: cannot find ml_results on local database to copy them to global database")
        return result

    def stop(self):
        self.keep_running = False
        self.engine.stop()

    def push_trial(self, x) -> str:
        for i in range(len(x)):
            if x[i] > 1:
                x[i] = 1
                logger.debug("OUT OF BOUNDS")
            if x[i] < 0:
                x[i] = 0
                logger.debug("OUT OF BOUNDS")

        x_real = list(self.problem_definition.domain.denormalize(x))
        return self.engine.push_trial(Trial(self.update_default_context(x_real), self.problem_definition.reset_instructions,
                                            self.get_theta(x_real)))

    def wait_for_result(self, uuid: str) -> TaskResult:
        return self.engine.wait_for_trial(uuid, 50).task_result

    def get_theta(self, x) -> dict:
        logger.debug("BaseService.get_theta(" + str(x) + ")")
        theta = dict()
        for i in range(len(self.problem_definition.domain.vector_mapping)):
            theta[self.problem_definition.domain.vector_mapping[i]] = x[i]

        return theta

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
        # logger.debug("BaseService.set_nested_parameter(dic: " + str(dic) + ", " + "keys: " + str(keys) + ")")
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
