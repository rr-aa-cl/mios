import logging
from threading import Thread
from queue import Queue
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from xmlrpc.client import ServerProxy
import time


logger = logging.getLogger("ml_service")

# not used anymore I think
class Task:  
    def __init__(self, problem_definition: ProblemDefinition, service_configuration: ServiceConfiguration, agents: list, service_url, knowledge_mode: str, knowledge_type: str):
        self.problem_definition = problem_definition
        self.service_configuration = service_configuration
        self.agents = agents
        self.service_url = service_url
        self.knowledge_mode = knowledge_mode
        self.knowledge_type = knowledge_type
        self.knowledge_tags = dict()


class TaskScheduler:

    def __init__(self, notification_user_token: str = "", notification_api_token: str = "", interface_port=8000):
        self.unassigned_tasks = Queue()
        self.assigned_tasks = set()
        self.services = set()
        self.keep_running = False
        self.kb_location = "localhost"
        self.interface_port=interface_port
        self.done_tasks = 0
        self.n_tasks = 0
        #self.pushover_client = Client(notification_user_token, api_token=notification_api_token)
        self.pushover_fail_cnt = 0

    def stop(self):
        self.keep_running = False

    def add_task(self, task: Task):
        self.unassigned_tasks.put(task)
        self.services.add(task.service_url)

    def solve_tasks(self, infinite: bool = False):
        logger.debug("TaskScheduler::solve_tasks.1")
        self.keep_running = True
        self.done_tasks = 0
        self.n_tasks = self.unassigned_tasks.qsize()
        t_message = time.time()
        while self.keep_running is True:
            logger.debug("TaskScheduler::solve_tasks.loop")
            if infinite is False:
                if self.done_tasks >= self.n_tasks:
                    self.keep_running = False
            if time.time() - t_message > 60:
                logger.info("Number of finished tasks: " + str(self.done_tasks))
                t_message = time.time()

            if self.unassigned_tasks.empty() is False:
                logger.debug("TaskScheduler::solve_tasks.queue_size1: " + str(self.unassigned_tasks.qsize()))
                task = self.unassigned_tasks.get()  # get next task
                self.unassigned_tasks.task_done()

                if self.is_service_ready(task.service_url, task.agents) is False:  # if task can not be started...
                    logger.debug("Could not assign task.")
                    self.unassigned_tasks.put(task)  # put it back
                    time.sleep(0.1)
                    continue
                else:  # if task can be started
                    self.assigned_tasks.add(task)
                    task_thread = Thread(target=self.solve_task, args=(task,))
                    task_thread.start()
            time.sleep(0.1)
            logger.debug("TaskScheduler::solve_tasks.after_pause")
        self.pushover_client.send_message("Experiment is done.", "Collective")

    def is_service_ready(self, service_url: str, agents: list) -> bool:
        logger.debug("TaskScheduler::is_service_ready(" + service_url + ", " + str(agents) + ")")
        s = ServerProxy("http://" + service_url + ":"+str(self.interface_port), allow_none=True)
        try:
            ready = s.is_ready(agents)
            logger.debug("TaskScheduler::is_service_ready.after_call")
            return ready
        except ConnectionRefusedError:
            logger.debug("TaskScheduler::is_service_ready.ConnectionRefusedError")
            return False

    def solve_task(self, task: Task):
        logger.debug("TaskScheduler::solve_task.starting at" +str(task.service_url)+" with task mode "+str(task.knowledge_mode))
        s = ServerProxy("http://" + task.service_url + ":"+str(self.interface_port), allow_none=True)
        knowledge_info = {
            "mode": task.knowledge_mode,
            "type": task.knowledge_type,
            "kb_location": self.kb_location,
            "kb_tags": task.knowledge_tags
        }
        try:
            s.start_service(task.problem_definition.to_dict(), task.service_configuration.to_dict(), task.agents, knowledge_info)
            if s.wait_for_service() is False:
                if self.pushover_fail_cnt < 1:
                    self.pushover_client.send_message("Learning task has failed.", "Collective")
                    self.pushover_fail_cnt += 1
                self.unassigned_tasks.put(task)  # put task back into queue
            logger.debug("TaskScheduler::solve_task.finished")
            self.done_tasks += 1
        except ConnectionRefusedError:
            pass
