from ml_service import mongodb_client
from mongodb_client.mongodb_client import MongoDBClient
from problem_definition.problem_definition import ProblemDefinition
from collective_manager.learning_config import LearningConfig
from python.examples import task
from utils.helper_functions import *
from run_experiments import *
from threading import Thread
import ipaddress
import subprocess
import random
from threading import Lock
from queue import PriorityQueue
from queue import Empty
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import socket
import os
import logging
import time

class InterfaceServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

logger = logging.getLogger("collective_manager")


class CollectiveModule:
    def __init__(self, hostname):
        ip_object = False
        try:
            ip_object = ipaddress.ip_address(hostname)
            result = subprocess.run(["avahi-resolve", "-a", str(ip_object)], stdout=subprocess.PIPE,check=True,text=True,shell=False).stdout
            hostname = result[result.find("\t")+1:result.find("\n")]
        except ValueError:
            self.hostname = hostname
        if hostname[-6:] == ".local":
            hostname = hostname[:-6]
        if hostname[-14:] != ".rsi.ei.tum.de":
            self.hostname = hostname + ".rsi.ei.tum.de"
        self.ip = None
        if ip_object:
            self.ip = str(ip_object)

        self.miosR_port = 13000
        self.miosL_port = 12000
        self.mongo_port = 27017
        self.mls_port = 8000
        self.current_task_left = "no Information"
        self.current_task_right = "no Information"
        self.status_left = "no Information"  # possible: "no Information", "not running", "Idle", "Reflex", "UserStopped"
        self.status_right = "no Information"  # possible: "no Information", "not running", "Idle", "Reflex", "UserStopped"
        self.object_left = "no Information"
        self.object_right = "no Information"
        self.mls = "no Information"  # possible: "no Information", "not running", "running", "busy"
        self.connectivity = "no Information"  # possible: "no Information", "not connected", "not pingalbe", "connected"
        self.arm_raised = False
        self.lc = None  # learning configuration for current problem
        self.lc_sequence = []  # list of learning configurations
        self.current_problem_uuid = None
        self.keep_monitoring = False
        self.monitoring_thread = None
        self.data_thread = None
        if self.ip:
            self.ml_service = ServerProxy("http://"+self.ip+":"+str(self.mls_port),allow_none=True)
            self.mongo = MongoDBClient(self.ip)
        
    def _get_ipv4_by_hostname(self, hostname):
        try:
            ips = list(
                i        # raw socket structure
                    [4]  # internet protocol info
                    [0]  # address
                for i in 
                socket.getaddrinfo(
                    hostname,
                    0  # port, required
                )
                if i[0] is socket.AddressFamily.AF_INET  # ipv4

                # ignore duplicate addresses with other socket types
                and i[1] is socket.SocketKind.SOCK_RAW  
            )
        except socket.gaierror:
            logger.debug("host "+self.hostname+" is not listed in the DNSserver")
            return False
        self.ip = ips[0]  # store only single ip
        return ips[0]

    def _ping(self):
        if self.ip:
            hostname = self.ip
        else:
            hostname = self.hostname
        response = os.system(f"ping -c 1 -w 1 {hostname} &> /dev/null")  #  1 ping with max duration of 1 second
        #^change this line to subprocess.run()^
        if response != 0:
            logger.error("host "+self.hostname+" is not pingable")
            return False
        else:
            return True

    def check_connectivity(self):
        if not self.ip:  # ask the DNS server
            if not self._get_ipv4_by_hostname(self.hostname):
                self.connectivity = "not connected"
                return False  # no DNS entry
        if not self._ping():  # ping the module
            self.connectivity = "not pingable"
            return False  # not pingable
        self.connectivity = "connected"
        return True
    
    def check_mios_state(self):
        if not self.ip:
            robot = self.hostname
        else:
            robot = self.ip
        response_miosL = call_method(robot, self.miosL_port,"get_state",timeout=1)    
        response_miosR = call_method(robot, self.miosR_port,"get_state",timeout=1)
        if not response_miosL:
            self.status_left = "not running"
            self.object_left = "no Information"
            self.current_task_left = "no Information"
            logger.error("mios-left on host "+self.hostname+" is not running.")    
        if not response_miosR:
            self.status_right = "not running"
            self.object_right = "no Information"
            self.current_task_right = "no Information"
            logger.error("mios-right on host "+self.hostname+" is not running.")
        if not response_miosL and not response_miosR:
            return False
        else:
            self.status_left = response_miosL["result"]["status"]
            self.status_right = response_miosR["result"]["status"]
            self.current_task_left = response_miosL["result"]["current_task"]
            self.current_task_right = response_miosR["result"]["current_task"]
            self.object_left = response_miosL["result"]["grasped_object"]
            self.object_right = response_miosR["result"]["grasped_object"]
            return True
    
    def check_mls(self):
        if not self.ml_service:
            self.ml_service = ServerProxy("http://"+self.ip+":"+str(self.mls_port),allow_none=True)
        if not self.ip:
            addr = self.hostname
        else:
            addr = self.ip
        try:
            busy = self.ml_service.is_busy()
        except ConnectionRefusedError:
            self.mls = "not running"
            logger.error("ml_service on host "+self.hostname+" is not running.")
            return False
        self.mls = "running"
        if busy:
            logger.debug("ml_service on host "+self.hostname+" is busy.")
            self.mls = "busy"
        return not busy
    
    def is_busy(self):
        if self.check_mls():
            return True
        if self.ip:
            robot = self.ip
        else:
            robot = self.hostname
        response_miosL = call_method(robot, self.miosL_port,"get_state",timeout=1)    
        response_miosR = call_method(robot, self.miosR_port,"get_state",timeout=1)
        if not response_miosL:
            self.status_left = "not running"
            self.object_left = "no Information"
            self.current_task_left = "no Information"
            logger.error("mios-left on host "+self.hostname+" is not running.")   
            return True 
        if not response_miosR:
            self.status_right = "not running"
            self.object_right = "no Information"
            self.current_task_right = "no Information"
            logger.error("mios-right on host "+self.hostname+" is not running.")
            return True
        if response_miosL and response_miosR:
            self.status_left = response_miosL["result"]["status"]
            self.status_right = response_miosR["result"]["status"]
            self.current_task_left = response_miosL["result"]["current_task"]
            self.current_task_right = response_miosR["result"]["current_task"]
            self.object_left = response_miosL["result"]["grasped_object"]
            self.object_right = response_miosR["result"]["grasped_object"]

        if response_miosL["result"]["current_task"] != "IdleTask":
            logger.debug("mios-left on host "+self.hostname+" is not on IdleTask")
            return True
        if response_miosR["result"]["current_task"] != "IdleTask":
            logger.debug("mios-right on host "+self.hostname+" is not on IdleTask")
            return True
        return False
        
    def get_state(self):
        state = {    "hostname":self.hostname,
                    "ip":self.ip,
                    "miosR_port": self.miosR_port,
                    "miosL_port": self.miosL_port,
                    "mongo_port": self.mongo_port,
                    "mls_port": self.mls_port,
                    "current_task_left": self.current_task_left,
                    "current_task_right": self.current_task_right, 
                    "status_left": self.status_left, 
                    "status_right": self.status_right, 
                    "object_left": self.object_left, 
                    "object_right": self.object_right, 
                    "mls": self.mls,    
                    "connectivity": self.connectivity,
                    "learning_config": None,
                    "time_epoch": time.time(),
                    "time": time.strftime("%Y-%m-%d  %H:%M:%S", time.localtime())
                }
        if self.lc:
            state["learning_config"] = self.lc.to_dict()
        
        return state

    def update_state(self):
        self.current_task_left = "no Information"
        self.current_task_right = "no Information"
        self.status_left = "no Information"
        self.status_right = "no Information"
        self.object_left = "no Information"
        self.object_right = "no Information"
        self.mls = "no Information"     
        self.connectivity = "no Information"
        if not self.check_connectivity():
            return self.get_state()
        if not self.check_mios_state():
            return self.get_state()
        self.check_mls()
        return self.get_state()
    
    def raise_hand(self):
        if self.arm_raised:
            return True
        count = 0
        result = False
        while not result:
            try:
                result = move_joint(self.ip, "raise_hand")["result"]["task_result"]["success"]
            except (KeyError, TypeError):
                pass
            count += 1
            if count > 3:
                return False
        self.arm_raised = True
        return True
    
    def move(self, pose, port=12000):
        count = 0
        result = False
        while not result:
            try:
                result = move_joint(self.ip, pose, wait=True,port=port)["result"]["task_result"]["success"]
            except (KeyError, TypeError):
                pass
            count += 1
            if count > 3:
                return False
        return True

    def set_learning_config(self, pd:ProblemDefinition, sc: ServiceConfiguration, knowledge:Knowledge, priority=0):
        '''
        setting the learning config inside here is ment to prevent conflicting task allocations from different experiments running in parallel
        also it is used for logging reasons
        '''
        self.lc = LearningConfig(pd,sc,knowledge, priority = priority)
        return True

    def remove_learning_config(self):
        self.lc = None
        return True
    
    def ready_to_learn(self, insertable=None):
        if not self.lc:
            logger.error("No Learning Configuration found.")
            return False
        self.update_state()
        if insertable is None:
            insertable = self.lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]
        if not self.object_left == insertable:
            return False
        if not self.object_right == "hold_"+insertable:
            return False
        return True

    def get_next_task(self):
        '''returns insertable of tasks in learning pipeline'''
        if not self.lc:
            return False
        return self.lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"] 

    def move_to_approach_pose(self, insertable):
        if not self.move("hold_"+insertable,13000):
            return False
        if not self.move(insertable+"container_above",12000):
            return False
        self.arm_raised=False
        return True
        
    def _run_monitoring(self):
        count = 0
        while self.keep_monitoring:
            time.sleep(5)
            self.update_state()
            if self.mls == "no Information":
                continue
            if self.mls == "running":
                continue
            if self.mls == "busy":
                count += 1
                if count == 100 and self.current_problem_uuid:
                    ml_results = self.mongo.read("ml_results","insertion",{"meta.uuid":self.current_problem_uuid})[0]
                    if len(ml_results) < 3:
                        logger.error("Module is not learning properly. Check it visually")
                continue
            if self.current_problem_uuid:
                ml_results = self.mongo.read("ml_results","insertion",{"meta.uuid":self.current_problem_uuid})[0]
                if "final_results" not in ml_results:
                    logger.error("Final results have not been written")
                    continue
                else:
                    self.current_problem_uuid = None
                    self.place_insertable(self.object_left)
            #set next problem:
            if self.lc_sequence:
                self.lc = self.lc_sequence.pop(0)
                self.move_camera(self.lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"])
                self.grasp_insertable(self.lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"])
                self.move_to_approach_pose(self.lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"])

            if self.lc:
                if self.object_left != self.lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]:
                    self.raise_hand()
                else:
                    self.move_to_approach_pose(self.lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"])
            self.stop_monitoring()
            
    def move_camera(self, inseratble):
        pass
    
    def place_insertable(self, insertable):
        place_insertable(self.ip,self.object_left,self.object_left+"_container",self.object_left+"_container_approach",self.object_left+"_container_above",12000)
    
    def grasp_insertable(self, insertable):
        grasp_insertable(self.ip,self.object_left,self.object_left+"_container",self.object_left+"_container_approach",self.object_left+"_container_above",12000)

    def _data_storing(self, mongo_id:str):
        while self.keep_monitoring:
            time.sleep(60)
            state = self.update_state()
            self.global_db.update("modules", self.hostname,{"_id": mongo_id},{str(int(state["time_epoch"])): state})
    
    def check_tags_unused(self, tags:list[str]):
        mongodb_client = MongoDBClient(self.ip)
        data = mongodb_client.read("ml_results","insertion",{"meta.tags":tags})
        if len(data) > 0:
            return False
        return True
    
    def start_monitoring(self, global_db_ip, experiment_name:str = "INVALID"):
        if self.monitoring_thread is not None or self.data_thread is not None:
            logger.error("Already monitoring")
            return False
        self.keep_monitoring = True
        self.update_state()
        self.global_db = MongoDBClient(global_db_ip)
        state = self.get_state()
        self.monitoring_thread = Thread(target=self._run_monitoring, name="monitoring")
        self.monitoring_thread.start()

        mongo_id = self.global_db.write("modules",self.hostname, {"meta":{"experiment":experiment_name, "learning_config":self.lc.to_dict()}, str(state["time_epoch"]): state})
        self.data_thread = Thread(target=self._data_storing, args=mongo_id, name="data_storing")
        self.data_thread.start()
        return mongo_id

    def stop_monitoring(self):
        self.keep_monitoring = False
        if self.monitoring_thread is not None:
            self.monitoring_thread.join()
            self.monitoring_thread = None
        if self.data_thread is not None:
            self.data_thread.join()
            self.data_thread = None

    def start_learning(self):
        '''
        uuid for learning pipeline (get when larning problem is appended to learning pipeline)
        '''
        if not self.lc:
            logger.error("no learning configuration added")
            return False
        insertable = self.lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]
        self.update_state()
        if self.connectivity != "connected":
            return False
        if self.status_left is not True or self.status_right is not True:
            return False
        if self.mls is not "running":
            return False
        if self.object_left != insertable:
            self.raise_hand()
            return False
        if self.object_right != "hold_"+insertable:
            self.raise_hand()
            return False
        if not self.move_to_approach_pose(insertable):
            logger.error("Cant move to approach pose")

            return False
        self.arm_raised = False
        s = ServerProxy("http://" + self.ip + ":"+str(self.mls_port), allow_none=True)
        self.current_problem_uuid = s.start_service(self.lc.pd.to_dict(), self.lc.sc.to_dict(), [self.lc.pd.host], self.lc.knowledge.to_dict())
        self.lc = None
        self.arm_raised = False
        return self.current_problem_uuid

    def check_pose(self, pose, side="left"):
        if side == "left":
            response = call_method(self.ip, 12000, "download_object_context", {"object": pose})
        else:
            response = call_method(self.ip, 13000, "download_object_context", {"object": pose})
        if type(response) is not dict:
            self.update_state()
            return False
        if "error" in response["result"]:
            return False
        return response["result"]["result"]  # response["result"]["context"]
    
    def finished(self, uuid):
        pass

    
class CollectiveExperiment:
    def __init__(self, name:str, modules:dict[str, CollectiveModule], problem_definitions:list[ProblemDefinition] = None, knowledge_configs:list[Knowledge] = None,
                  service_configs:list[ServiceConfiguration] = None, n_agents:int = False, keep_allocation:bool = False, global_db_ip:str = "10.157.175.119"):
        '''
        modules: dict of CollectiveModules used in this experiment; {"<hostname>": CollectiveModule(), ...}
        '''
        self.name = name
        self.modules = modules
        self.global_db_ip = global_db_ip
        self.problem_definitions = problem_definitions
        self.knowledge_configs = knowledge_configs
        self.service_configs = service_configs
        self.n_agents = n_agents  # number of concurrently learning agents
        self.keep_allocation = keep_allocation
        self.fast_knowledge_pipe_host = socket.gethostname()
        self.keep_running = False
        self.finished = False
        self.task_allocation_thread = None
        self.ready = False
        self.learning_queue = PriorityQueue()
        self.learning_threads = []

        self.exp_state = dict()
        self.exp_state["state"] = "not started"  #  "uncompleted" "completed"  
        for i,_ in enumerate(problem_definitions):
            self.exp_state["s"+str(i)] = {}
            self.exp_state["s"+str(i)]["module"] = problem_definitions[i].host
            self.exp_state["s"+str(i)]["skill_class"] = problem_definitions[i].skill_class
            self.exp_state["s"+str(i)]["skill_instance"] = problem_definitions[i].skill_instance
            self.exp_state["s"+str(i)]["state"] = "not started"  # queued, started, learned, 
            self.exp_state["s"+str(i)]["t_start"] = False
            self.exp_state["s"+str(i)]["t_end"] = False
            self.exp_state["s"+str(i)]["external_knowledge"] = []  # knowledge found in the beginning of the task (slow pipe)
        
        self.fast_knowledge_pipe = dict()
        self.tasks = dict()
        for i,pd in enumerate(self.problem_definitions):
            #check if module is available
            if pd.host not in self.modules.keys():
                logger.error("Problem Definition referese to host that is not part of the experiment: " + pd.host)
                continue
            #create task dictionary
            if pd.host not in self.tasks:
                self.tasks[pd.host] = []
            self.tasks[pd.host].append({"insertable":pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"],
                                        "index":i,
                                        "mls_uuid": None})
            
    def get_modules(self):
        return self.modules

    def get_next_task(self):
        pass

    def precheck(self):
        for pd in self.problem_definitions:
            if pd.host not in self.modules.keys():
                logger.error("Problem Definition referese to host that is not part of the experiment: " + pd.host)
                return False
            module = self.modules[pd.host]
            module.update_state()
            if not module.check_pose(pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]):
                return False
            if not module.check_pose(pd.default_context["skills"]["insertion"]["skill"]["objects"]["Container"]):
                return False
            if not module.check_pose(pd.default_context["skills"]["insertion"]["skill"]["objects"]["Approach"]):
                return False
            if not module.check_pose(pd.default_context["skills"]["insertion"]["skill"]["objects"]["Container"]+"_above"):
                return False
            if not module.check_pose("hold_"+pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"], "right"):
                return False
            if not module.check_pose("raise_hand"):
                return False
            #check if tags are already available at Module
            if not module.check_tags_unused(pd.tags):
                logger.warning("Tags are alreay in use: "+str(pd.tags))
                return False

        return True
            
    def _task_allocation(self):
        '''
        this implements a task allocation that strictly allocated according to the input sequence (FIFO)
        '''
        all_queued = False
        index = 0
        while True:
            n_tasks = len(self.exp_state) - 1  # "state" key in self.exp_state is not an actual task
            for i in range(n_tasks):
                if self.exp_state["s"+str(i)]["state"] == "not started":  # found next task that is not started
                    module = self.exp_state["s"+str(i)]["module"]
                    insertable = self.exp_state["s"+str(i)]["skill_instance"]
                    lc = LearningConfig(pd=self.problem_definitions[i],
                                            sc=self.service_configs[i],
                                            knowledge=self.knowledge_configs[i])
                    if self.modules[module].ready_to_learn(insertable):  # if object are grasped
                        if self.modules[module].lc is None:
                            self.modules[module].set_learning_config(pd=lc.pd, sc=lc.sc, knowledge=lc.knowledge)
                        self.learning_queue.put((index, lc))
                        self.exp_state["s"+str(i)]["state"] = "queued"
                        index += 1
                        break
                    elif self.modules[module].lc is None:  #set next lc (so module raises arm)
                        self.modules[module].set_learning_config(pd=lc.pd, sc=lc.sc, knowledge=lc.knowledge)
                    elif self.name not in self.modules[module].lc.pd.tags:
                        logger.error("different experiment is blocking next task: " + str(lc.pd.tags))
                        time.sleep(3)
                        break
                    break
                all_queued = True
            if all_queued:
                break
        return True
    
    def _learner_thread(self):
        while self.keep_running:
            # get next task
            index, lc = self.learning_queue.get(block=True, timeout=None) # wait until a task is in the queue
            module = lc.pd.host
            insertable = lc.pd.default_context["skills"]["insertion"]["skill"]["objects"]["Insertable"]
            if self.modules[module].lc is None:
                self.modules[module].set_learning_config(lc.pd, lc.sc, lc.knowledge)
            if self.name not in self.modules[module].lc.pd.tags:
                logger.error("Wrong learning configuration loaded to module (other experiments running?)")
                self.learning_queue.put((index,lc))
                time.sleep(1)
                continue
            if not self.modules[module].ready_to_learn():
                self.learning_queue.put((index,lc))
                time.sleep(1)
                continue
            mls_uuid = self.modules[module].start_learning()
            if not mls_uuid:
                self.learning_queue.put((index,lc))
                time.sleep(1)
                continue
            self.tasks[module]["mls_uuid"] = mls_uuid
            self.exp_state["s"+str(index)]["state"] = "started"
            while self.modules[module].finished(mls_uuid):
                time.sleep(3)
            self.exp_state["s"+str(index)]["state"] = "learned"

    def run_experiment(self):

        #assume prechecks are done
        #put tasks into learning queue:
        if not self.keep_allocation:
            # throw all tasks in learning-queue at once, if worker thread takes task which is not able to start it will be put back 
            # (this can change the allocation sequence)
            # baiscally it is a greedy allocation strategy that learnes a task as soon as it is available.
            index = 0
            for pd,sc,knowledge in zip(self.problem_definitions, self.service_configs, self.knowledge_configs):
                self.learning_queue.put((index, LearningConfig(pd=pd, sc=sc, knowledge=knowledge)), block=False)
                index += 1
        else:
            # create thread that shovels next tasks (according to allocation sequence) into learning-queue only if they can be started imediatly
            self.task_allocation_thread = Thread(target=self._task_allocation)
            self.task_allocation_thread.start()

        for module in self.modules.values():
            module.start_monitoring(self.global_db_ip, self.name)
        
        for i in range(self.n_agents):
            self.learning_threads.append(Thread(target=self._learner_thread, name="leaner"+str(i)))
            self.learning_threads[-1].start()
        # problem queue fifo and solved list
        # go through problem queue and assign next possible or next task to worker thread -> running heap
        # worker threads n_agents
        
        # START MODULE SUPERVISIONS threads
        start learning if first n_agents are ready
        ToDo: add RPC for fast knowledge pipe in second thread
        self.keep_running = True
        while self.keep_running:
            pass

    def stop_experiment(self):
        self.keep_running = False

    def append_task(self, module, pd, knowledge_config, sc):
        # append also self.exp_state
        pass
    
    def push_trial(self, task: str, theta: list, cost: float, keep_size: int = 1000000):
        '''
        part of the fast knowledge sharing pipe!
        the trial (theta) will be stored in self.data_storage under key "<task>" {"<name of origin>": Tuple(Theta, Cost, list(already requested by agents))}
        the stored trials will not exceed keep_size
        always the trial which was used by the most agents will be poped
        '''
        TODO: add mongodb to fast knowledge pipe
        logger.debug("push_trial: store trial from "+task)
        if task not in self.fast_knowledge_pipe:
            self.fast_knowledge_pipe[task] = []
        if len(self.fast_knowledge_pipe[task]) >= keep_size:  # delte the trial that was requested the most already
            index = -1
            requested_from_n_others = 0
            for i in range(len(self.fast_knowledge_pipe[task])):  # pop the trial which was already requested by the most other agents
                if len(self.fast_knowledge_pipe[task][i])>requested_from_n_others:
                    index = i
                    requested_from_n_others = len(self.fast_knowledge_pipe[task][i])
            logger.warning("knowlege_manager.push_trial: Delete Trial fromo Datastroage because of keep_size="+str(keep_size)+". Trial was forwarded to "+str(requested_from_n_others)+" others.")
            self.fast_knowledge_pipe[task].pop(index)
        self.fast_knowledge_pipe[task].append((theta, cost, []))
        self.fast_knowledge_pipe[task].sort(key=lambda t: t[1] )  # sort according to cost
        
    def request_trials(self, task:str, n_trials: int, similarity: dict = {}) -> list:
        '''
        part of the fast knowledge sharing pipe!
        self.fast_knowledge_pipe: {"<name of origin>": Tuple(Theta, Cost, list(already requested by agents))}
        
        sends back a list of tuples: [Tuple(Theta, Cost, Origin)]   where origin is the agent where the trial originated
        the list will be of size n_trials

        '''
        TODO: add mongodb to fast knowledge pipe

        data_storage_keys = list(self.fast_knowledge_pipe.keys())
        if n_trials<1:
            logger.debug("KnowledgeManager.request_trials: requested less than 1 trial -> return False")
            return []
        random.shuffle(data_storage_keys)
        if data_storage_keys == []:
            return []
        try:
            data_storage_keys.pop(data_storage_keys.index(task))  # neglet requesting agent
        except ValueError:
            pass 
        try:
            similarity.pop(task)  # neglet requesting agent
        except KeyError:
            pass 
        
          # if no similarity is given: initialise with equal probability
        for key in data_storage_keys:
            if key not in similarity:
                similarity[key] = 1  # assume good similarity at first
        for key in list(similarity.keys()):
            if key not in data_storage_keys:
                similarity.pop(key)
        trials=[]
        n_available_trials = 0
        for a in range(len(data_storage_keys)):
            for t in self.fast_knowledge_pipe[data_storage_keys[a]]:
                if task in t[2]:  # check if trial was already forwarded to agent
                    continue
                n_available_trials += 1
        if n_available_trials <= n_trials:  # we dont have enougth trials -> take everything
            for a in range(len(data_storage_keys)):
                for t in self.fast_knowledge_pipe[data_storage_keys[a]]:
                    if task not in t[2]:  # if trials wasn't already sent to agent
                        trials.append((t[0],t[1],data_storage_keys[a]))
                        t[2].append(task)  # save agent name for this trial
        else:
            for key in similarity.keys():
                if similarity[key] <= 0:
                    similarity[key] = 0.01 
            similarity_sum = sum(similarity.values())
            for key in similarity.keys():
                similarity[key] = similarity[key] / similarity_sum  # calculate probability for picking trial from this agent (=key)
            index = 0  # go throu the data_storage and add one trial from every agent, repeat afterwards
            while(n_trials > len(trials)):
                source_task = str(np.random.choice(data_storage_keys, p=[similarity[key] for key in similarity.keys()]))  # random pick an agent according to probability
                for t in self.fast_knowledge_pipe[source_task]:
                    if task not in t[2]:
                        trials.append((t[0],t[1],source_task))
                        t[2].append(task)
                        break
                if index < 100:  # index = count
                    index +=1
                else:
                    break
        return trials
        

class CollectiveManager:
    def __init__(self, modules:list = None, database="10.157.175.119"):
        '''
        Point of interaction with the collective (PD.RAI)
        Inputs: modules: list - list of hostnames of the modules that will be managed with this class
                database: str - hostname or ip of MongoDB
        '''
        self.rpc_port = 8006
        self.module_names = set()
        self.modules = dict()
        if type(modules) is list:
            self.module_names = set(modules)
            self._update_modules()
        self.database_ip = database
        self.database_client = MongoDBClient(database)
        
        self.experiments = dict()
        self.running_experiments = set()
        self.experiment_threads = dict()
        self.rpc_server = InterfaceServer(("0.0.0.0", self.rpc_port), allow_none=True)
    
    def start_rpc_server(self):
        logger.debug("CollectiveManager started on port "+str(self.rpc_port))
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.add_experiment, "add_experiment")
        self.rpc_server.register_function(self.start_experiment, "start_experiment")
        self.rpc_server.register_function(self.add_module, "add_module")
        self.rpc_server.register_function(self.remove_module, "remove_module")
        self.rpc_server.register_function(self.get_experiments, "get_experiments")
        self.rpc_server.register_function(self.get_modules, "get_modules")
        self.rpc_server.register_function(self.describe_experiment, "describe_experiment")
        self.rpc_server.register_function(self.remove_experiment, "remove_experiment")
        self.rpc_server.serve_forever()
        logger.debug("CollectiveManager stopped")
    
    def add_module(self, module):
        '''
        Adds an module (hostname) to the managed collective
        '''
        if type(module) is list:
            for a in module:
                self.module_names.add(a)
        elif type(module) is str:
            self.module_names.add(module)
        else:
            logger.error("Invalid input type. Accepted input is list or str.")
            return False
        return self._update_modules()

    def remove_module(self, module):
        if type(module) is list:
            for a in module:
                self.module_names.remove(a)
        elif type(module) is str:
            self.module_names.remove(module)
        else:
            logger.error("Invalid input type. Accepted input is list or str.")
            return False
        return self._update_modules()

    def _update_modules(self):
        #remove deleted ones:
        remove_these = []
        for a in self.modules.keys():
            if a not in self.module_names:
                remove_these.append(a)
        for a in remove_these:
            self.modules[a].delete()
            self.modules.pop(a)
        #add new ones:
        for a in self.module_names:
            if a not in self.modules:
                self.modules[a] = CollectiveModule(a)
        return len(self.modules) == len(self.module_names)

    def add_experiment(self, name:str, modules:list, problem_definitions:list, knowledge_configs:list, service_configs:list, 
                       n_agents:int = False, keep_allocation:bool = False):
        '''
        Adds experiment definitions to be executed on the collective. All input lists have to have the same order
        input:  name: str
                This is the name of this single experiment, eg. "charlie_1"
        
                modules: list
                This list has the same length as the problem_definitons list. It contains all hostnames for the single learning problems. 
        
                problem_definitons: list
                The list can contain problem_definitions dicts directly (like the ones created with InsertionFactory get_proble_definition())
                Or it can contain all insertables. With this option, the problem_definions are created automatically for insertion 
                with default values and a norm for naming poses.

                knowledge_configs: list
                This is a list of dicts containing the knowledge configurations for the every problem_definiton that is learned.
                If there is only one dict inside the list, it is used for every problem_definition.

                service_configs: list
                This is a list of dicts containing the service configurations for the every problem_definiton that is learned.
                If there is only one dict inside the list, it is used for every problem_definition.

                n_agents: int
                This sets the number of concurrent learning modules

                keep_allocation: bool
                If True, the sequence of problems is keept during the experiment
                If False, this sequence is allowed to change to increase learning throughput
        '''
        #check type:
        if type(problem_definitions) != list or type(knowledge_configs) != list or type(service_configs) != list:
            logger.error("Type of input is not matching type(list)")
            return False
        #check length:
        if len(modules) != len(problem_definitions):
            logger.error("Length of modules and problem_definitions doesn\'t match.")
            return False
        if len(problem_definitions) != len(service_configs):
            if len(service_configs) == 1:
                service_configs = service_configs*len(problem_definitions) #same service config for all problems
            else:
                logger.error("Number of service_configs (" + str(len(service_configs)) + 
                             ") does\'t match number of problem_definitions (" + str(len(problem_definitions)))
                return False  
        if len(problem_definitions) != len(knowledge_configs) :
            if len(knowledge_configs) == 1:
                knowledge_configs = knowledge_configs*len(problem_definitions) #same service config for all problems
            else:
                logger.error("Number of knowledge_configs (" + str(len(knowledge_configs)) + 
                             ") does\'t match number of problem_definitions (" + str(len(problem_definitions)))
                return False
        #check if modules are managed by collective manager
        for module in modules:
            if module not in self.module_names:
                return False
            
        for i,pd in enumerate(problem_definitions):
            #check type
            if type(pd) is tuple:
                #create full problem_definitions
                pd = InsertionFactory([modules[i]], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": pd[1], "Container": pd[1]+"_container",
                                    "Approach": pd[1]+"_container_approach"}).get_problem_definition(pd[1])
            elif type(pd) is dict:
                pd = ProblemDefinition.from_dict(pd)
            else:
                logger.error("Falty problem_definition type discovered: " + str(type(pd)))
                return False
            pd.tags.append(name)
            pd.host = modules[i]

        if name in self.experiments:
            self.experiments[name].problem_definitions.extend(problem_definitions)
            self.experiments[name].knowledge_configs.extend(knowledge_configs)
            self.experiments[name].service_configs.extend(service_configs)
        else:
            self.experiments[name] = CollectiveExperiment(name = name,
                                                          modules={name: module for name, module in self.modules.items() if module.hostname in modules},
                                                          problem_definitions=problem_definitions,
                                                          knowledge_configs=knowledge_configs,
                                                          service_configs=service_configs,
                                                          n_agents=n_agents,
                                                          keep_allocation=keep_allocation,
                                                          global_db_ip=self.database_ip)
    
    def remove_experiment(self, name:str):
        if self.experiments[name].keep_running:
            self.experiments[name].stop()
            self.experiment_threads[name].join()
            self.running_experiments.remove(name)
        
        self.experiments.pop(name)
        return True

    def start_experiment(self, name):
        if name not in self.experiments:
            logger.error("No experiment available with name "+name)
            return False
        self.running_experiments.add(name)
        if name in self.experiment_threads:
            logger.error("Experiment with name "+str(name)+" is already running")
            return False
        precheck = self.experiments[name].precheck()
        if not precheck:
            return {"precheck": precheck}
        self.experiment_threads[name] = Thread(target=self.experiments[name].run_experiment)
        self.experiment_threads[name].start()
        return True
    
    def get_experiments(self):
        return list(self.experiments.keys())

    def get_modules(self):
        return list(self.modules)
    
    def describe_experiment(self, name):
        running = True if name in self.running_experiments else False
        return {"running": running, "tasks": self.experiments[name].tasks}
    

class CollectiveClient:
    def __init__(self):
        self.collective_manager_ip = None
    



        


        
        
    


