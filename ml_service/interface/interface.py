from lib2to3.pytree import Node
import logging
from threading import Thread
from threading import Lock
import uuid
import time

from services.generic_optimizer import GenericOptimizerService
from services.cmaes import CMAESService
from services.cmaes import CMAESConfiguration
from services.svm import SVMService
from services.svm import SVMConfiguration
from services.base_service import ServiceConfiguration
from problem_definition.problem_definition import ProblemDefinition
from utils.ws_client import call_method
from database.database import Database

from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
from xmlrpc.client import ServerProxy

logger = logging.getLogger("ml_service")


class InterfaceServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class Interface:
    """Class that provides basic controlling functions for ml_service"""

    def __init__(self, interface_port=8000, mios_port=12000, mongo_port=27017):
        self.service = None
        self.learn_thread = None
        self.rpc_server = None
        self.mios_port = mios_port
        self.interface_port = interface_port
        self.mongo_port = mongo_port
        self.service_lock = Lock()
        self.global_db = Database(self.interface_port+1, self.mongo_port)
        self.global_db_thread = None
        self.rpc_server = InterfaceServer(("0.0.0.0", interface_port), allow_none=True)
        self.start_global_database()

    def start_rpc_server(self):
        logger.debug("Interface::start_rpc_server() on port "+str(self.interface_port)+" with mios_port="+str(self.mios_port))
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.start_service_wrapper, "start_service")
        self.rpc_server.register_function(self.is_busy, "is_busy")
        self.rpc_server.register_function(self.wait_for_service, "wait_for_service")
        self.rpc_server.register_function(self.is_ready, "is_ready")
        self.rpc_server.register_function(self.stop_service, "stop_service")
        self.rpc_server.register_function(self.pause_service, "pause_service")
        self.rpc_server.register_function(self.resume_service, "resume_service")
        self.rpc_server.register_function(self.status, "status")
        self.rpc_server.serve_forever()
        logger.debug("Interface::start_rpc_server.server_stopped")

    def stop_rpc_server(self):
        logger.debug("Interface::stop_rpc_server()")
        # t = Thread(target=self.rpc_server.shutdown())
        # t.start()
        self.rpc_server.server_close()
        self.rpc_server.shutdown()
        logger.debug("Interface::stop_rpc_server.end")

    def start_service_wrapper(self, problem_definition: dict, configuration: dict, agents, knowledge: dict = None):
        logger.debug("Interface::start_service_wrapper")
        if configuration["service_name"] == "cmaes":
            service_configuration = CMAESConfiguration()
            service_configuration.from_dict(configuration)
        elif configuration["service_name"] == "svm":
            service_configuration = SVMConfiguration()
            service_configuration.from_dict(configuration)

        self.start_service(ProblemDefinition.from_dict(problem_definition), service_configuration, set(agents),
                           knowledge)

    def start_service(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                      agents: set, knowledge: dict = None) -> str:
        logger.debug("Interface::start_service")
        if self.service_lock.acquire(blocking=False) is False:
            return "INVALID"

        if problem_definition.self_check() is False:
            return "INVALID"
        problem_definition.uuid = str(uuid.uuid4())
        if configuration.service_name == "cmaes":
            self.service = CMAESService()
        elif configuration.service_name == "svm":
            self.service = SVMService()
        elif configuration.service_name == "generic":
            self.service = GenericOptimizerService()
        else:
            logger.error("Service with name " + configuration.service_name + " does not exist.")
            return "INVALID"

        self.learn_thread = Thread(target=self.learn_task, args=(problem_definition, configuration, agents, knowledge),
                                   daemon=False)
        self.learn_thread.start()
        return problem_definition.uuid

    def learn_task(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                   agents: set, knowledge: dict) -> bool:
        logger.debug("Interface::learn_task")
        """strt to learn a task according to instructions"""
        try:
            logger.debug("interface.learn_task: start learning task")
            if self.service.initialize(problem_definition, configuration, agents, knowledge) is False:
                return False
            logger.debug("Service initialized ")
            result = self.service.learn_task()
            logger.debug("learning success " + str(result))
            return result
        finally:
            logger.debug("Interface::learn_task.finally: Releasing service lock")
            self.service_lock.release()

    def stop_service(self):
        logger.debug("Interface::stop_service")
        """Stop the learning process, if possible save all results and stop the robot"""
        if self.service is not None:
            self.service.stop()
    
    def pause_service(self):
        logger.debug("Interface::Pause()")
        if self.service is not None:
            self.service.pause()
    
    def resume_service(self):
        logger.debug("Interface::resume()")
        if self.service is not None:
            self.service.start()

    def is_ready(self, agents) -> bool:
        if self.service_lock.locked() is True:
            logger.debug("Interface::is_ready.locked")
            return False
        for a in agents:
            logger.debug("Interface::is_ready.before_call")
            print("############################################################################")
            response = call_method(a, self.mios_port, "is_busy")
            print("############################################################################2")
            logger.debug("Interface::is_ready.after_call")
            if response["result"]["busy"] is True:
                logger.debug("Interface::is_ready.agent_busy")
                return False

        return True

    def is_busy(self) -> bool:
        logger.debug("Interface::is_busy.locked: " + str(self.service_lock.locked()))
        return self.service_lock.locked()
    
    def status(self, agent: str = "localhost") -> dict:
        """"return status of service: [learning, thinking, ready, ]"""
        response = {}
        response["is_busy"] = self.service_lock.locked()
        mios_state = call_method(agent, self.mios_port, "get_state")
        if mios_state is not None:
            if "current_task" in mios_state["result"]:
                response["current_task"] = mios_state["result"]["current_task"]
            else:
                response["current_task"] = "INVALID"
        return response

    def wait_for_service(self):
        logger.debug("Interface::wait_for_service")
        while self.is_busy():
            time.sleep(1)
        if self.service == None:
            return None
        result = self.service.result
        del self.service
        self.service = None
        return result

    def start_global_database(self):
        logger.debug("interface.start_global_database")
        self.global_db_thread = Thread(target=self.global_db.start_server, daemon=False)
        self.global_db_thread.start()
        return True

    def stop_global_database(self):
        logger.debug("interface.stop_global_database")
        addr = "http://localhost:" + str(self.global_db.port) + "/"
        with ServerProxy(addr) as proxy:
            i = proxy.stop_server()
        self.global_db_thread.join(3)
        logger.debug("interface.stop_global_database: global Database hase been stoped, " + str(
            not self.global_db_thread.is_alive()))
        return not self.global_db_thread.is_alive()

    def get_status(self) -> str:
        """returns a detailed status for debugging purposes"""
        pass

    def download_results(self):
        """returns the results of a learned task from the Database"""
        pass
