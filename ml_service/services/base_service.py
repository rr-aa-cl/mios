import logging
from abc import ABCMeta
from abc import abstractmethod
from threading import Thread

import socket
import time
import numpy as np
import socket
import copy

from engine.engine import Engine
from engine.engine import Trial
from engine.engine import TaskResult
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.problem_definition import Domain
from knowledge_processor.knowledge_manager import KnowledgeManager
from mongodb_client.mongodb_client import MongoDBClient
from utils.exception import *
from services.knowledge import Knowledge
#from rpc_visualization.data_buffer import DataBuffer

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
    def __init__(self, mios_port=12000, mongo_port=27017):

        self.engine = None
        self.mios_port = mios_port
        self.mongo_port = mongo_port
        self.problem_definition = ProblemDefinition("NullSkill", "NullSkill", Domain(dict(), dict()), dict(), [], [],
                                                    [], None, None)
        self.knowledge_manager = KnowledgeManager(port=self.mongo_port)
        self.DBclient = MongoDBClient(port=self.mongo_port)  # for local ml_data
        self.globalDBclient = None
        self.engine_thread = None
        self.configuration = None
        self.keep_running = False
        self.pause_execution = False
        self.centroid = None
        self.result = False
        self.database_results_id = None
        #self.knowledge_source = None
        #self.knowledge = False
        self.skill_identity = dict()
        self.confidence = None
        self.host_name = socket.gethostname()
        self.knowledge = Knowledge()
        self.initial_knowledge_list = []  # this one is used for knowledge.type == "all": it stores all knowledge found in a list
        self.similarity_estimate = {}  # this maps a similarity to all collective agents 
        self.external_success = {}     # will be filled for each external Task with 1 for success or 0 if not
        self.internal_success = []     # counts just the internal trials: 1 for success 0 for failure
        # self.data_buffer_visualization = DataBuffer()
        self.test_debug = 0
        self.delta_time = 0
        self.starting_time = time.time()
        self.info={}  # a dict with information about the learning process (like experimant name or info for storing...)
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
                   agents: set, knowledge_source: dict = None, info:dict={}) -> (bool, str):
        self.problem_definition = problem_definition
        self.configuration = configuration
        self.info=info
        #self.knowledge_source = knowledge_source
        #self.data_buffer_visualization = DataBuffer()
        if knowledge_source is not None:
            self.knowledge.from_dict(knowledge_source)
        self.starting_time = time.time()  # starting time of learning before first trial (used to retrief knowledge)
        # Skill identity used for searching similar tasks:
        self.skill_identity = {"tags": problem_definition.tags, "skill_class": problem_definition.skill_class,
                               "skill_instance": problem_definition.skill_instance,
                               "optimum_weights": problem_definition.cost_function.optimum_weights}

        if self.problem_definition.is_valid() is False:
            logger.error("Problem definition is not valid.")
            return False
        logger.debug("base_service.initialize(): "+str(self.knowledge.similarity))
        if self.knowledge.similarity is not None:
            logger.debug("base_service.initialize(): initialize knowledge manager with similarity relationsships")
            self.knowledge_manager.init_similarity(self.knowledge.similarity)
        if self.knowledge.parameters is not None:
            logger.debug("base_service.initialize(): Use given parameters as initial knowlege.")
            if self.knowledge.confidence is None:
                self.knowledge.confidence = 0.04
        elif self.knowledge.mode == None:
            self.centroid = None
            self.configuration.request_probability = 0  # posible AttributeError for non SVM learner
            self.knowledge.kb_location = None
        elif self.knowledge.mode == "specific":
            logger.debug("BaseService::initialize: Use specific knowledge: "+str(self.knowledge.tags))
            client = MongoDBClient(self.knowledge.kb_location)
            self.knowledge = self.knowledge_manager.get_knowledge_by_filter(client, self.knowledge.kb_db,
                                                                                self.knowledge.kb_task_type,
                                                                                {"meta.tags": {"$all": self.knowledge.scope}}
                )
        elif self.knowledge.mode == "only_fast_pipe":
            logger.debug(f"BaseService::initialize: Use only knowledge over fast knowledge pipe (no initial knowledge): "+str(self.knowledge.tags))
            logger.debug(f"initial request probability: {self.configuration.request_probability}")   # posible AttributeError for non SVM learner
            
        elif self.knowledge.mode == "local":
            logger.debug("base_service.initialize(): get local knowlege")
            if self.knowledge.type == "similar":
                self.knowledge.from_dict(self.knowledge_manager.get_similar_knowledge(
                        self.problem_definition.get_task_identifier(), self.knowledge.scope))
            elif self.knowledge.type == "predicted":
                self.knowledge.from_dict(self.knowledge_manager.get_predicted_knowledge(self.problem_definition.skill_class,
                                                                                    self.knowledge.scope,
                                                                                    self.problem_definition.identity)
                )
            elif self.knowledge.type == "all":
                self.initial_knowledge_list = self.knowledge_manager.get_knowledge(self.problem_definition.get_task_identifier(), self.knowledge.scope)
                self.knowledge.parameters = []
                self.knowledge.uuid = []
                for i in range(len(self.initial_knowledge_list)):
                    knowlege = Knowledge()
                    knowlege.from_dict(self.initial_knowledge_list[i])
                    self.initial_knowledge_list[i] = knowlege
                    self.initial_knowledge_list[i].update()
                    self.knowledge.parameters.append(self.initial_knowledge_list[i].parameters)
                    self.knowledge.uuid.append(self.initial_knowledge_list[i].uuid)
            else:
                logger.error("base_service: dont understand knowledge type"+str(self.knowledge.type))
        elif self.knowledge.mode == "global":
            self.globalDBclient = MongoDBClient(self.knowledge.kb_location)
            logger.debug("base_service::initialize(): get global knowlege")
                  # change this to direct acccess to MongoDB at global DB. 
                # figure out a way to pre-enter a similarity dict to knowledge-manager (bidirectional to mongodb)
            try:
                if self.knowledge.type == "similar":
                    self.knowledge.from_dict(self.knowledge_manager.get_similar_knowledge(self.problem_definition.get_task_identifier(), self.knowledge.scope,
                                                                knowledge_db="global_knowledge",
                                                                data_db="global_ml_results",
                                                                location=self.knowledge.kb_location)
                    )
                elif self.knowledge.type == "predicted": 
                    raise NotImplementedError
                    
                elif self.knowledge.type == "all":
                    self.delta_time = time.time()-self.starting_time
                    self.knowledge.time_range[1] = self.knowledge.time_range[1]+self.delta_time
                    #self.initial_knowledge_list = kb.get_knowledge(self.problem_definition.get_task_identifier(), self.knowledge.scope, self.knowledge.time_range)
                    self.initial_knowledge_list = self.knowledge_manager.get_knowledge(self.problem_definition.get_task_identifier(), self.knowledge.scope, 
                                                                                        time_range=self.knowledge.time_range, knowledge_db="global_knowledge",location=self.knowledge.kb_location)
                    logger.debug("base_service::initialize(): get all knowledge. Found "+str(len(self.initial_knowledge_list)))
                    self.knowledge.parameters = []
                    self.knowledge.uuid = []
                    for i in range(len(self.initial_knowledge_list)):
                        knowlege = Knowledge()
                        knowlege.from_dict(self.initial_knowledge_list[i])
                        self.initial_knowledge_list[i] = knowlege
                        self.initial_knowledge_list[i].update()
                        self.knowledge.parameters.append(self.initial_knowledge_list[i].parameters)
                        self.knowledge.uuid.append(self.initial_knowledge_list[i].uuid)

                else:
                    logger.error("base_service: dont understand knowledge type"+str(self.knowledge.type))
            except socket.timeout:
                logger.error("base_service: global Database is not reachable!")
            except ConnectionRefusedError:
                logger.error("base_service: global Database is not reachable!")
                pass
        else:
            logger.error("base_service::initialize(): Unknown knowledge mode " + str(self.knowledge.mode))
        
        if self.knowledge.parameters and not self.initial_knowledge_list:
            if type(self.knowledge.parameters) == dict:  # only single knowledge parameter set given
                self.centroid = []
                if len(self.knowledge.parameters) != len(self.problem_definition.domain.limits):
                    logger.error("Domain sizes do not match!")
                    return False
                for key in self.knowledge.parameters:
                    self.centroid.append(self.knowledge.parameters[key])
                logger.debug("base_service.initialize(): Use global knowledge " + str(self.centroid))
                self.centroid = self.problem_definition.domain.normalize(np.asarray(self.centroid))
                self.confidence = self.knowledge.confidence
            if type(self.knowledge.parameters) == list:  # multiple knowledge sets are given
                for parameters in self.knowledge.parameters:
                    knowledge = copy.deepcopy(self.knowledge)
                    knowledge.parameters = parameters
                    self.initial_knowledge_list.append(knowledge)
                    logger.debug("append knowledge.parameters to initial_knowledge_list")
        else:
            logger.debug("base_service.initialize(): No Knowledge used as initial centroid!!!")

        if self.knowledge.similarity is not None and self.initial_knowledge_list:
            for i in range(len(self.initial_knowledge_list)-1,-1,-1):
                obj = self.initial_knowledge_list[i].skill_instance
                if obj in self.knowledge.similarity:
                    if self.knowledge.similarity[obj] <= 0:  # if request probability is zero, dont use it as init knowledge
                        self.initial_knowledge_list.pop(i)
                        logger.warning("remove entry from init_knowledge_list because it does not go together with knolẃledge.similarity")

        logger.info("Given knowledge sets: "+str(len(self.initial_knowledge_list)))
        self.knowledge_manager.fast_pipe_ip = self.knowledge.kb_location
        self.engine = Engine(agents, mios_port=self.mios_port, mongo_port=self.mongo_port)
        self.database_results_id = self.engine.initialize(self.problem_definition, self.configuration.exploration_mode)

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
        ml_data[0]["meta"]["init_knowledge"] = self.knowledge.to_dict()
        ml_data[0]["final_results"]["confidence"] = self.confidence
        self.DBclient.update("ml_results", self.problem_definition.skill_class, {"_id": self.database_results_id},
                             ml_data[0])

        new_knowledge = self.knowledge_manager.get_knowledge_by_id(self.DBclient,
                                                                    self.problem_definition.get_task_identifier(), self.database_results_id)  #ml_data[0]["_id"]
        if new_knowledge:
            new_knowledge["meta"]["tags"] = self.problem_definition.tags
            new_knowledge["meta"]["uuid"] = self.problem_definition.uuid
            new_knowledge["meta"]["kb_location"] = self.knowledge.kb_location
            new_knowledge["meta"]["type"] = self.knowledge.type
            new_knowledge["meta"]["mode"] = self.knowledge.mode
            if not new_knowledge["parameters"]:
                logger.error("base_service.learn_task: New produced knowledge does have parameters!")
            print("Learning completed")

            self.knowledge_manager.store_knowledge(self.DBclient, new_knowledge, self.problem_definition.tags)   #store knowledge with problem_definition tags
            if self.knowledge.mode == "global":
                logger.debug("base_service.learn_task: store new knowledge to global database at " + str(self.knowledge.kb_location ))
                if not self.globalDBclient:
                    self.globalDBclient = MongoDBClient(self.knowledge.kb_location)
                self.knowledge_manager.store_knowledge(self.globalDBclient,new_knowledge,self.problem_definition.tags,"global_knowledge")
            
        else:
            logger.debug("Base_service.learn_task(): No knowledge could be created from ml_results.")
        
        
        if not self.globalDBclient and self.knowledge.kb_location:
            self.globalDBclient = MongoDBClient(self.knowledge.kb_location)
        if self.globalDBclient:
            if "exp_name" in self.info and "iteration" in self.info:
                self.globalDBclient.write(self.info["exp_name"], "iteration_"+str(self.info["iteration"]), ml_data[0])
            self.globalDBclient.write("global_ml_results", self.problem_definition.skill_class, ml_data[0])
        return result

    def stop(self):
        self.keep_running = False
        if self.engine is not None:
            self.engine.stop()

    def pause(self):
        self.pause_execution = True
        if self.engine is not None:
            self.engine.pause()

    
    def start(self):
        self.pause_execution = False
        if self.engine is not None:
            self.engine.resume()

    def push_trial(self, x, external: dict = False) -> str:
        if external:
            try:
                logger.debug("BaseService: Push trial to engine, external (fast knowledge pipe)="+str(external["skill_instance"]))
            except KeyError:
                try:
                    logger.debug("BaseService: Push trial to engine, external (initial knowledge)="+str(external["meta"]["skill_instance"]))
                except KeyError:
                    logger.debug("BaseService: Push trial to engine, external (some Knowledge)="+str(external))
        else:
            logger.debug("BaseService: Push trial to engine, external=False")
        while self.pause_execution and self.keep_running:
            logger.debug("base_service.push_trial: Paused...")
            time.sleep(1)

        for i in range(len(x)):
            if x[i] > 1:
                x[i] = 1
                logger.debug("OUT OF BOUNDS")
            if x[i] < 0:
                x[i] = 0
                logger.debug("OUT OF BOUNDS")

        x_real = list(self.problem_definition.domain.denormalize(x))
        return self.engine.push_trial(
            Trial(self.update_default_context(x_real), self.problem_definition.reset_instructions,self.problem_definition.rescue_instructions,
                  self.get_theta(x_real), external=external))

    def wait_for_result(self, uuid: str) -> TaskResult:
        result = self.engine.wait_for_trial(uuid, 50 * self.problem_definition.n_variations)
        result_dict = result.to_dict()
        if result_dict["external"]:  # if external is not False
            if type(result_dict["external"]) is str:
                result_dict["external"] = eval(result_dict["external"])  # make it a dict again from string
        # self.data_buffer_visualization.add_data(self.make_float_again(result_dict))
        return result.task_result

    def get_theta(self, x) -> dict:
        #logger.debug("BaseService.get_theta(" + str(x) + ")")
        theta = dict()
        for i in range(len(self.problem_definition.domain.vector_mapping)):
            theta[self.problem_definition.domain.vector_mapping[i]] = float(x[i])
        return theta
    
    def get_params(self, theta) -> list:
        params = []
        for i in range(len(self.problem_definition.domain.vector_mapping)):
            params.append(theta[self.problem_definition.domain.vector_mapping[i]])
        return params

    def update_default_context(self, x) -> dict:
        # logger.debug("BaseService.update_default_context(" + str(x) + ")")
        theta = dict()
        updated_context = self.problem_definition.default_context
        for i in range(len(self.problem_definition.domain.vector_mapping)):
            theta[self.problem_definition.domain.vector_mapping[i]] = float(x[i])

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
    
    def make_float_again(self, x):
        if isinstance(x, np.float64):
            return float(x)
        elif isinstance(x, dict):
            for key in x.keys():
                x[key] = self.make_float_again(x[key])
        elif isinstance(x, list):
            for i in range(len(x)):
                x[i] = self.make_float_again(x[i])
        return x
