import logging
from threading import Thread
from threading import Lock
from threading import Event, RLock
import uuid
import time

from services.generic_optimizer import GenericOptimizerService
from services.cmaes import CMAESService
from services.cmaes import CMAESConfiguration
from services.svm import SVMService
from services.svm import SVMConfiguration
from services.orig_psp import OrigPSPService
from services.orig_psp import OrigPSPConfiguration
from services.base_service import ServiceConfiguration
from problem_definition.problem_definition import ProblemDefinition
from utils.ws_client import call_method
from database.database import Database
from utils.cmd_loop import CMDLoop
#from rpc_visualization.switcher import TensorboardClient
#from collective_manager.video_recorder import FFMpegWebcamRecorder

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
        self.cmd_loop = None
        self.mios_port = mios_port
        self.interface_port = interface_port
        self.mongo_port = mongo_port
        self.service_lock = Lock()
        self.lifecycle_lock = RLock()
        self.stop_requested = Event()
        self.stop_failed = False
        self.global_db = Database(self.interface_port+1, self.mongo_port)
        self.global_db_thread = None
        self.rpc_server = InterfaceServer(("0.0.0.0", interface_port), allow_none=True, logRequests=False)

        # rpc_visulation related 
        self.telemetry_buffer = None
        self.keep_running_telemetry = False
        self.telemetry_sender = None
        self.telemetry_thread = None

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
        self.rpc_server.register_function(self.start_cmd_loop, "start_cmd_loop")
        self.rpc_server.register_function(self.stop_cmd_loop, "stop_cmd_loop")
        # self.rpc_server.register_function(self.start_telemetry, "start_telemetry")
        # self.rpc_server.register_function(self.stop_telemetry, "stop_telemetry")
        # self.rpc_server.register_function(self.test_video_recording, "test_video_recording")
        self.rpc_server.serve_forever()
        logger.debug("Interface::start_rpc_server.server_stopped")

    def stop_rpc_server(self):
        logger.debug("Interface::stop_rpc_server()")
        # t = Thread(target=self.rpc_server.shutdown())
        # t.start()
        self.rpc_server.server_close()
        self.rpc_server.shutdown()
        logger.debug("Interface::stop_rpc_server.end")

    def start_service_wrapper(self, problem_definition: dict, configuration: dict, agents, knowledge: dict = None, info:dict={}):
        logger.debug("Interface::start_service_wrapper")
        if configuration["service_name"] == "cmaes":
            service_configuration = CMAESConfiguration()
            service_configuration.from_dict(configuration)
        elif configuration["service_name"] == "svm":
            service_configuration = SVMConfiguration()
            service_configuration.from_dict(configuration)
        elif configuration["service_name"] == "origPSP":
            service_configuration = OrigPSPConfiguration()
            service_configuration.from_dict(configuration)
        logger.debug("starting service with problem definition ="+str(problem_definition["tags"]))
        return self.start_service(ProblemDefinition.from_dict(problem_definition), service_configuration, set(agents),
                           knowledge, info)

    def start_service(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                      agents: set, knowledge: dict = None, info:dict={}) -> str:
        logger.debug("Interface::start_service")
        with self.lifecycle_lock:
            if self.is_busy() or not self.service_lock.acquire(blocking=False):
                return "INVALID"
            # Publish the cancellation latch before a constructor can block on I/O.
            self.stop_requested = Event()
            self.service = None
            self.learn_thread = None
        worker_started = False
        try:
            if problem_definition.self_check() is False:
                return "INVALID"
            factories = {"cmaes": CMAESService, "svm": SVMService,
                         "origPSP": OrigPSPService, "generic": GenericOptimizerService}
            factory = factories.get(configuration.service_name)
            if factory is None:
                logger.error("Service with name %s does not exist.", configuration.service_name)
                return "INVALID"
            problem_definition.uuid = str(uuid.uuid4())
            service = factory(self.mios_port, self.mongo_port)
            with self.lifecycle_lock:
                self.service = service
                self.learn_thread = Thread(
                    target=self.learn_task,
                    args=(problem_definition, configuration, agents, knowledge, info), daemon=False)
                self.learn_thread.start()
                worker_started = True
            return problem_definition.uuid
        finally:
            if not worker_started:
                with self.lifecycle_lock:
                    self.service_lock.release()

    def learn_task(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                   agents: set, knowledge: dict, info:dict={}) -> bool:
        logger.debug("Interface::learn_task")
        """start to learn a task according to instructions"""
        result = False
        service = self.service
        try:
            if self.stop_requested.is_set():
                return False
            logger.debug("interface.learn_task: start learning task")
            if service.initialize(problem_definition, configuration, agents, knowledge,info) is False:
                return False
            if self.stop_requested.is_set():
                return False
            logger.debug("Service initialized ")
            # self.telemetry_buffer = self.service.data_buffer_visualization
            result = service.learn_task()
            logger.debug("learning success " + str(result))
        finally:
            # Keep this run busy until all engine workers have exited, including
            # when initialization or the optimizer raises an exception.
            with self.lifecycle_lock:
                if self.cmd_loop is not None:
                    self.cmd_loop.request_stop()
                self.stop_failed = not self._stop_learning_service(service)
            if service.engine_thread is not None and service.engine_thread.ident is not None:
                service.engine_thread.join()
            with self.lifecycle_lock:
                cmd_stopped = self.stop_cmd_loop()
                self.stop_failed = self.stop_failed or not cmd_stopped
                logger.debug("Interface::learn_task.finally: Releasing service lock")
                self.service_lock.release()
        return result
    
    def stop_service(self):
        """Request learning cancellation; keep the XML-RPC server running.

        True acknowledges the stop request, not physical standstill. Callers
        must also wait for is_busy() == False and confirm Core is idle.
        """
        logger.debug("Interface::stop_service")
        with self.lifecycle_lock:
            self.stop_requested.set()
            if self.cmd_loop is not None:
                self.cmd_loop.request_stop()
            stopped = True
            if self.service is not None and (self.service_lock.locked() or self.stop_failed):
                stopped = self._stop_learning_service(self.service)
            # Request the learning stop before optional command-loop cleanup.
            cmd_stopped = self.stop_cmd_loop()
            self.stop_failed = not (stopped and cmd_stopped)
            return not self.stop_failed

    @staticmethod
    def _stop_learning_service(service):
        try:
            return service.stop() is True
        except Exception:
            logger.exception("Learning stop request failed; retry stop_service.")
            return False
    
    def pause_service(self):
        logger.debug("Interface::Pause()")
        with self.lifecycle_lock:
            if self.service is not None:
                self.service.pause()
    
    def resume_service(self):
        logger.debug("Interface::resume()")
        with self.lifecycle_lock:
            if self.stop_requested.is_set() or self.stop_failed:
                return False
            if self.service is not None:
                return self.service.start()
            return False

    def is_ready(self, agents) -> bool:
        if self.is_busy():
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
        #logger.debug("Interface::is_busy.locked: " + str(self.service_lock.locked()))
        return self.service_lock.locked() or self.stop_failed
    
    def status(self, agent: str = "localhost") -> dict:
        """"return status of service: [learning, thinking, ready, ]"""
        response = {}
        response["is_busy"] = self.is_busy()
        mios_state = call_method(agent, self.mios_port, "get_state")
        if mios_state is not None:
            if "current_task" in mios_state["result"]:
                response["current_task"] = mios_state["result"]["current_task"]
            else:
                response["current_task"] = "INVALID"
        return response

    def wait_for_service(self):
        logger.debug("Interface::wait_for_service")
        while True:
            with self.lifecycle_lock:
                if not self.is_busy():
                    if self.service is None:
                        return None
                    result = self.service.result
                    self.service = None
                    return result
            time.sleep(1)

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

    def start_cmd_loop(self, cmd):
        logger.debug("interface::start_cmd_loop() with cmd:\n"+str(cmd))
        with self.lifecycle_lock:
            if self.stop_failed:
                return False
            if not self.cmd_loop:
                self.cmd_loop = CMDLoop(cmd)
                self.cmd_loop.start()
                return True
            return False
    
    def stop_cmd_loop(self):
        logger.debug("interface::stop_cmd_loop()")
        with self.lifecycle_lock:
            if self.cmd_loop:
                try:
                    if self.cmd_loop.stop() is not True:
                        return False
                except Exception:
                    logger.exception("Command-loop stop failed; retry stop_service.")
                    return False
                self.cmd_loop = None
        logger.debug("interface::stop_cmd_loop: stopped successfully")
        return True

    # def start_telemetry(self, ip, port):
    #     logger.debug("interface::start_telemetry with ip "+str(ip)+" and port "+str(port))
    #     self.keep_running_telemetry = True
    #     self.telemetry_sender = TensorboardClient(ip, port)
    #     if self.telemetry_buffer is None:
    #         return False
    #     self.telemetry_thread = Thread(target=self._send_telemetry)
    #     self.telemetry_thread.start()
    #     return True

    # def stop_telemetry(self):
    #     self.keep_running_telemetry = False
    #     logger.debug("interface::stop_telemetry"+str(self.keep_running_telemetry))
    #     if self.service is not None:
    #         self.service.data_buffer_visualization.add_data("STOP")
            
    #     if self.telemetry_thread is not None:
    #         self.telemetry_thread.join()
    #         self.telemetry_thread = None

    # def _send_telemetry(self):
    #     while self.keep_running_telemetry:
    #         buffered_trial = self.telemetry_buffer.get_data(timeout=1)
    #         if buffered_trial is None:
    #             continue
    #         if buffered_trial == "STOP":
    #             break
    #         logger.debug("_send_telemetry to " + str(self.telemetry_sender.ip)) 
    #         if not self.telemetry_sender.send(buffered_trial):
    #             self.telemetry_buffer.add_data(buffered_trial)
    #             logger.error("cannot send trial to "+ str(self.telemetry_sender.ip)+":"+str(self.telemetry_sender.port))
    #             time.sleep(2)
    #     logger.debug("interface:: telemetry sending thread stopped.")
    #     return True
    
    def test_video_recording(self,folder, filename, video_path="/dev/v4l/by-path/pci-0000:00:14.0-usb-0:7:1.3-video-index0"):
        logger.debug("start video recording test")
        self.video_recorder = FFMpegWebcamRecorder(video_path)
        if not self.video_recorder.start_stream(
                                                output_folder=folder,
                                                base_filename=filename,
                                                compressed=False,rotate=True,
                                                framerate="30",
                                                resolution="1920x1080",
                                                pixel_format="yuyv422"
                                                ):
            logger.error("!!!!Cannot start video recording!!!!")
        time.sleep(5)
        logger.debug("stop video recording test")
        return self.video_recorder.stop_stream()
                

    def get_status(self) -> str:
        """returns a detailed status for debugging purposes"""
        pass

    def download_results(self):
        """returns the results of a learned task from the Database"""
        pass
