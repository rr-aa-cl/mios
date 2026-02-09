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
import threading
import socket
import redis
import json
import math

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
        self.global_db = Database(self.interface_port+1, self.mongo_port)
        self.global_db_thread = None
        self.rpc_server = InterfaceServer(("0.0.0.0", interface_port), allow_none=True, logRequests=False)

        # rpc_visulation related 
        self._stop_telemetry = threading.Event()
        self.redisClient = None
        self.telemetry_threads = []

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
        self.rpc_server.register_function(self.start_telemetry, "start_telemetry")
        self.rpc_server.register_function(self.stop_telemetry, "stop_telemetry")
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
        if self.service_lock.acquire(blocking=False) is False:
            return "INVALID"

        if problem_definition.self_check() is False:
            return "INVALID"
        problem_definition.uuid = str(uuid.uuid4())
        if configuration.service_name == "cmaes":
            self.service = CMAESService(self.mios_port,self.mongo_port)
        elif configuration.service_name == "svm":
            self.service = SVMService(self.mios_port,self.mongo_port)
        elif configuration.service_name == "origPSP":
            self.service = OrigPSPService(self.mios_port,self.mongo_port)
        elif configuration.service_name == "generic":
            self.service = GenericOptimizerService(self.mios_port,self.mongo_port)
        else:
            logger.error("Service with name " + configuration.service_name + " does not exist.")
            return "INVALID"

        self.learn_thread = Thread(target=self.learn_task, args=(problem_definition, configuration, agents, knowledge, info),
                                   daemon=False)
        self.learn_thread.start()
        return problem_definition.uuid

    def learn_task(self, problem_definition: ProblemDefinition, configuration: ServiceConfiguration,
                   agents: set, knowledge: dict, info:dict={}) -> bool:
        logger.debug("Interface::learn_task")
        """start to learn a task according to instructions"""
        result = False
        try:
            logger.debug("interface.learn_task: start learning task")
            if self.service.initialize(problem_definition, configuration, agents, knowledge,info) is False:
                return False
            logger.debug("Service initialized ")
            result = self.service.learn_task()
            logger.debug("learning success " + str(result))
        finally:
            logger.debug("Interface::learn_task.finally: Releasing service lock")
            self.stop_cmd_loop()
            self.stop_telemetry(agents)
            self.service_lock.release()
        return result
    
    def stop_service(self):
        logger.debug("Interface::stop_service")
        """Stop the learning process, if possible save all results and stop the robot"""
        self.stop_cmd_loop()
        if self.service is not None:
            if self.service.engine is not None:
                self.stop_telemetry(self.service.engine.agents)
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
        #logger.debug("Interface::is_busy.locked: " + str(self.service_lock.locked()))
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

    def start_cmd_loop(self, cmd):
        logger.debug("interface::start_cmd_loop() with cmd:\n"+str(cmd))
        if not self.cmd_loop:
            self.cmd_loop = CMDLoop(cmd)
            self.cmd_loop.start()
    
    def stop_cmd_loop(self):
        logger.debug("interface::stop_cmd_loop()")
        if self.cmd_loop:
            self.cmd_loop.stop()
        self.cmd_loop = None
        logger.debug("interface::stop_cmd_loop: stopped successfully")

    def start_telemetry(self, agents, ip, username, password, port=6379):
        logger.debug("interface::start_telemetry with ip "+str(ip)+" and port "+str(port))
        self._stop_telemetry.clear()
        try:
            self.redisClient = redis.Redis(
                    # host="redis-master.global", 
                    host=ip, 
                    port=port, 
                    db=0, 
                    decode_responses=True,
                    username=username,
                    password=password,
                    # password="QqJ3JDqNjN",
                    socket_connect_timeout=2,    # Fail if can't connect in 2 second
                    socket_timeout=2             # Fail if operations take > 2 second
                 )
            self.redisClient.ping()
            logger.info("connect to redis")
        except redis.RedisError as e:
            logger.info("Redis error failed: " + str(e))
        except redis.AuthenticationError:
            logger.info("Redis authentication failed (wrong password: " + str(e))
        except redis.ConnectionError as e:
            logger.info("Redis connection failed: " + str(e))
        except Exception as e:
            logger.info("Unexpected error: " + str(e))

        t = Thread(target=self._send_trial_result)
        t.start()
        self.telemetry_threads.append(t)
        receiving_port = 8371
        for agent in agents:
            t = Thread(target=self._subscribe_telemetry, args=(agent, agent, receiving_port, ["O_F_ext_K"]))
            t.start()
            self.telemetry_threads.append(t)
            receiving_port+=1
        return True

    def stop_telemetry(self, agents):
        self._stop_telemetry.set()
        logger.debug("interface::stop_telemetry")
        for robot_ip in agents:
            call_method(robot_ip, self.mios_port, "unsubscribe_telemetry",{"ip":robot_ip})
        if self.service is not None:
            self.service.data_buffer_visualization.add_data("STOP")           
        if self.telemetry_threads is not None and len(self.telemetry_threads) > 0:
            for tele_thread in self.telemetry_threads:
                tele_thread.join(timeout=5)
                tele_thread = None
    
    def _send_trial_result(self):
        logger.info("----------start telemetry trial result")

        while not self._stop_telemetry.is_set():
            if self.service.data_buffer_visualization is None:
                time.sleep(1)
                continue
            buffered_trial = self.service.data_buffer_visualization.get_data(timeout=1)
            if buffered_trial is None:
                continue
            if buffered_trial == "STOP":
                break
            logger.info("-------------------_send_telemetry to redis") 
            logger.info(str(buffered_trial))
            try:   
                self.redisClient.lpush(
                    "ml_result",
                    json.dumps(
                        {
                            "arm_label": buffered_trial["agent"],
                            "trial_count": buffered_trial["trial_number"],
                            "is_succeed": buffered_trial["task_result"]["q_metric"]["success"]
                        }
                    ),
                )
            except redis.RedisError as e:
                logger.error("Redis push data failed: " + str(e)) 
        logger.debug("interface:: telemetry sending thread stopped.")
        return True


   #  useful functions:
    def _subscribe_telemetry(self, robot_ip, receiving_ip, receiving_port, data:list):
        '''
        let mios send current state
        robot_ip - where mios is running
        reveiving_ip, receiving_port - where do you want to receive the data
        data - list of strings; what kind of data do you whish. Possible strings:
            //End effector pose in origin frame (O).
                            "O_T_EE",
                        //End effector pose in task frame (TF).
                            "T_T_EE",
                        //Link-side joint pose.
                            "q"
                        //Link-side joint velocities.
                            "dq"
                        //Motor-side joint pose.
                            "theta"
                        //Motor-side joint velocities.
                            "dtheta"
                        //Cartesian twist in origin frame (O).
                            "O_dX_EE"
                        //Cartesian twist in end effector frame (EE).
                            "EE_dX_EE"
                        //Cartesian twist in task frame (TF).
                            "TF_dX_EE"
                        //Estimated external torques.
                            "tau_ext"
                        //Joint torques.
                            "tau_j"
                        //Estimated external wrench at TCP in stiffness frame (K).
                            "K_F_ext_K"
                        //Derivative of estimated external wrench at TCP in stiffness frame (K).
                            "K_dF_ext_K"
                        //Estimated external wrench at TCP in origin frame (O).
                            "O_F_ext_K"
                        //Derivative of estimated external wrench at TCP in origin frame (O).
                            "O_dF_ext_K"
                        //Estimated external wrench at TCP in task frame (TF).
                            "TF_F_O_T_EEext_K"
                        //Derivative of estimated external wrench at TCP in task frame (TF).
                            "TF_dF_ext_K"
                            "finger_width"
                            "finger_temperature"
                            "is_grasping"
                        //Mass matrix.
                            "M"
                        //Coriolis vector.
                            "C"
                        //Gravity vector.
                            "G"
                        //Body jacobian.
                            "B_J_EE"
                        //Zero jacobian. 
                            "B_J_O"
                            "max_finger_width"
                            "hand_activity_state"
                        //Rho factor from force controllers's shaping function.
                            "e"
                            "rho"
                            "K_x"
                            "xi_x"
                            "K_theta"
                            "xi_theta"
                            "TF_T_EE_d"
                            "TF_dX_d"
                            "TF_F_ff"
                            "O_R_T"
                            "q_d"
                            "dq_d"
                            "tau_ff"

        '''
        logger.info("----------start telemetry gentleness result")
        call_method(robot_ip, self.mios_port, "subscribe_telemetry",{"subscribe":data,"ip":receiving_ip,"port":receiving_port})
        robot_state = self._write_incomming_udp(receiving_ip, receiving_port)
        call_method(robot_ip, self.mios_port, "unsubscribe_telemetry",{"subscribe":data,"ip":receiving_ip,"port":receiving_port})

        return robot_state


    def _write_incomming_udp(self, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((ip, port))
            s.settimeout(1)  # <-- key: makes recvfrom() wake up periodically

            logger.info("UDP listening on %s:%d", ip, port)

            while not self._stop_telemetry.is_set():
                try:
                    data, addr = s.recvfrom(65535)  # buffer size
                except socket.timeout:
                    continue  # check stop flag again
                except OSError:
                    # socket closed or other OS-level interruption
                    break

                data_dict = json.loads(data.decode("utf-8"))
                for key, value in data_dict.items():
                    if type(value) == list:
                        if key == "O_F_ext_K":
                            gentleness=math.sqrt(value[0] ** 2 + value[1] ** 2 + value[2] ** 2)/math.sqrt(3)
                            percentage = (gentleness/20)*100
                            self.redisClient.lpush(
                                "gentleness",
                                json.dumps(
                                    {
                                        "arm_label": ip,
                                        "percentage": percentage
                                    }
                                )
                            )
                    else: 
                        logger.info("key %d value %d ", key, value)

        except Exception:
            logger.exception("Error in _write_incoming_udp on %s:%d", ip, port)
        finally:
            try:
                s.close()
            except Exception:
                pass
            logger.info("UDP thread exiting for %s:%d", ip, port)


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
