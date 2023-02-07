import logging
from abc import ABCMeta
from abc import abstractmethod
from threading import Thread
from xmlrpc.client import ServerProxy
import socket
import time
import numpy as np

from engine.engine import Engine
from engine.engine import Trial
from engine.engine import TaskResult
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.problem_definition import Domain
from knowledge_processor.knowledge_manager import KnowledgeManager
from mongodb_client.mongodb_client import MongoDBClient
from utils.exception import *

logger = logging.getLogger("ml_service")


class ServiceConfiguration(metaclass=ABCMeta):
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.exploration_mode = False

    def to_dict(self) -> dict:
        config_dict = self._to_dict()
        config_dict["service_name"] = self.service_name
        config_dict["exploration_mode"] = self.exploration_mode
        return config_dict

    def from_dict(self, config_dict):
        self._from_dict(config_dict)
        self.service_name = config_dict["service_name"]
        self.exploration_mode = config_dict["exploration_mode"]

    @abstractmethod
    def _to_dict(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def _from_dict(self, config_dict: dict):
        raise NotImplementedError


class BaseService(metaclass=ABCMeta):
    def __init__(self):

        self.engine = None
        self.problem_definition = ProblemDefinition("NullSkill", "NullSkill", Domain(dict(), dict()), dict(), [], [],
                                                    [], None, None)
        self.knowledge_manager = KnowledgeManager()
        self.DBclient = MongoDBClient()  # for local ml_data
        self.engine_thread = None
        self.configuration = None
        self.keep_running = False
        self.centroid = None
        self.result = False
        self.database_results_id = None
        self.knowledge_source = None
        self.knowledge = False
        self.skill_identity = dict()
        self.confidence = None
        self.host_name = socket.gethostname()

        # 10s timeout for xmlrpc clinet:
        socket.setdefaulttimeout(10)

    @abstractmethod
    def _initialize(self):
        raise NotImplementedError

    @abstractmethod
    def _learn_task(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _terminate(self):
        raise NotImplementedError

    @abstractmethod
    def _is_learned(self) -> bool:
        raise NotImplementedError

    def initialize(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                   agents: set, knowledge_source: dict = None) -> (bool, str):
        self.problem_definition = problem_definition
        self.configuration = configuration
        self.knowledge_source = knowledge_source
        # Skill identity used for searching similar tasks:
        self.skill_identity = {"tags": problem_definition.tags, "skill_class": problem_definition.skill_class,
                               "skill_instance": problem_definition.skill_instance,
                               "optimum_weights": problem_definition.cost_function.optimum_weights}

        if self.problem_definition.is_valid() is False:
            logger.error("Problem definition is not valid.")
            return False

        if knowledge_source is not None:
            logger.debug("BaseService::initialize: Contacting database at " + "http://" + knowledge_source[
                "kb_location"] + ":8001")
            knowledge_type = knowledge_source.get("type", "similar")
            if knowledge_source["mode"] == 'none':
                self.centroid = None
            elif knowledge_source["mode"] == "specific":
                print("#######################KNOWLEDGE############################")
                print(knowledge_source["scope"])
                client = MongoDBClient(knowledge_source["kb_location"])
                self.knowledge = self.knowledge_manager.get_knowledge_by_filter(client, knowledge_source["kb_db"],
                                                                                knowledge_source["kb_task_type"],
                                                                                {"meta.tags": {
                                                                                    "$all": knowledge_source["scope"]}})
            elif knowledge_source["mode"] == 'local':
                logger.debug("base_service.initialize(): get local knowlege")
                if knowledge_type == "similar":
                    self.knowledge = self.knowledge_manager.get_similar_knowledge(
                        self.problem_definition.get_task_identifier(), knowledge_source["scope"])
                elif knowledge_type == "predicted":
                    self.knowledge = self.knowledge_manager.get_predicted_knowledge(self.problem_definition.skill_class,
                                                                                    self.knowledge_source["scope"],
                                                                                    self.problem_definition.identity)
                    print("#########################################")
                    print(self.knowledge)
                else:
                    self.knowledge = False
            elif knowledge_source["mode"] == 'global':
                logger.debug("base_service::initialize(): get global knowlege")
                logger.debug("base_service::initialize(): contacting database at http://" + knowledge_source[
                    "kb_location"] + ":8001")
                with ServerProxy("http://" + knowledge_source["kb_location"] + ":8001") as kb:
                    try:
                        if knowledge_type == "similar":
                            self.knowledge = kb.get_similar_knowledge(self.problem_definition.get_task_identifier(),
                                                                      knowledge_source["scope"])
                        elif knowledge_type == "predicted":
                            self.knowledge = kb.get_predicted_knowledge(self.problem_definition.skill_class,
                                                                        self.knowledge_source["scope"],
                                                                        self.problem_definition.identity)
                        else:
                            self.knowledge = False
                    except socket.timeout:
                        logger.error("base_service: global Database is not reachable!")
                    except ConnectionRefusedError:
                        pass
            elif knowledge_source["parameters"]:
                self.knowledge = dict()
                self.knowledge["parameters"] = knowledge_source["parameters"]
                self.knowledge["meta"] = dict()
                self.knowledge["meta"]["confidence"] = 0.04
            else:
                logger.error("base_service::initialize(): Unknown knowledge mode " + str(knowledge_source["mode"]))

            if self.knowledge:
                self.centroid = []
                if len(self.knowledge["parameters"]) != len(self.problem_definition.domain.limits):
                    logger.error("Domain sizes do not match!")
                    return False
                for key in self.knowledge["parameters"]:
                    self.centroid.append(self.knowledge["parameters"][key])
                logger.debug("base_service.initialize(): Use global knowledge " + str(self.centroid))
                self.centroid = self.problem_definition.domain.normalize(np.asarray(self.centroid))
                self.confidence = self.knowledge["meta"].get("confidence")

        self.engine = Engine(agents)
        self.database_results_id = self.engine.initialize(self.problem_definition, configuration.exploration_mode)

        self._initialize()

        self.engine_thread = Thread(target=self.engine.main_loop)
        self.engine_thread.start()

        while self.engine.keep_running is False:
            logger.debug("Service_base.initialize(): Wait unitl engine thread is running.")
            time.sleep(0.1)

    def learn_task(self) -> bool:
        self.keep_running = True
        try:
            result = self._learn_task()
        except StopService:
            result = False
        self.keep_running = False
        self.result = result

        self.engine_thread.join()  # wait for engine to write final results

        ml_data = self.DBclient.read("ml_results", self.problem_definition.skill_class, {"_id": self.database_results_id})
        if len(ml_data) != 1:
            logger.error(
                "base_service.learn_task: cannot find ml_results on local database to copy them to global database")
            return False
        ml_data[0]["meta"]["init_knowledge"] = dict()
        ml_data[0]["meta"]["init_knowledge"]["content"] = self.knowledge
        ml_data[0]["meta"]["init_knowledge"]["source"] = self.knowledge_source
        ml_data[0]["final_results"]["confidence"] = self.confidence

        # knowledge = self.knowledge_manager.get_knowledge_by_identity(self.DBclient,
        #                                                             self.problem_definition.get_task_identifier())
        # print("################################################")
        # print(knowledge)
        # self.knowledge_manager.store_knowledge(self.DBclient, knowledge, self.knowledge_source["scope"])

        if self.knowledge_source is not None:
            if self.knowledge_source["mode"] == "global":
                logger.debug("base_service.learn_task: store ml_results to global database at " + str(
                    "http://" + self.knowledge_source["kb_location"] + ":8001"))
                with ServerProxy("http://" + self.knowledge_source["kb_location"] + ":8001", allow_none=True) as kb:
                    try:
                        kb.store_result(ml_data[0])
                        kb.process_knowledge(self.problem_definition.get_task_identifier())
                    except socket.timeout:
                        logger.error("base_service: global Database is not reachable!")

        self.DBclient.update("ml_results", self.problem_definition.skill_class, {"_id": self.database_results_id},
                             ml_data[0])
        return result

    def stop(self):
        self.keep_running = False
        if self.engine is not None:
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
        return self.engine.push_trial(
            Trial(self.update_default_context(x_real), self.problem_definition.reset_instructions,
                  self.get_theta(x_real)))

    def wait_for_result(self, uuid: str) -> TaskResult:
        return self.engine.wait_for_trial(uuid, 50 * self.problem_definition.n_variations).task_result

    def get_theta(self, x) -> dict:
        logger.debug("BaseService.get_theta(" + str(x) + ")")
        theta = dict()
        for i in range(len(self.problem_definition.domain.vector_mapping)):
            theta[self.problem_definition.domain.vector_mapping[i]] = x[i]

        return theta

    def update_default_context(self, x) -> dict:
        # logger.debug("BaseService.update_default_context(" + str(x) + ")")
        theta = dict()
        updated_context = self.problem_definition.default_context
        for i in range(len(self.problem_definition.domain.vector_mapping)):
            theta[self.problem_definition.domain.vector_mapping[i]] = x[i]

        # logger.debug("BaseService.update_default_context.theta: " + str(theta))

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
            dic[p_name][p_dim - 1] = value

    def nested_get(self, input_dict, nested_key):
        internal_dict_value = input_dict
        for k in nested_key:
            internal_dict_value = internal_dict_value.get(k, None)
            if internal_dict_value is None:
                return None
        return internal_dict_value
