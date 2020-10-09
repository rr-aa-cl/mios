import logging
import sys
from threading import Thread
from queue import Queue
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from xmlrpc.client import ServerProxy
import time


logger = logging.getLogger("ml_service")


class Task:
    def __init__(self, problem_definition: ProblemDefinition, service_configuration: ServiceConfiguration, agents: list, service_url, knowledge_mode: str):
        self.problem_definition = problem_definition
        self.service_configuration = service_configuration
        self.agents = agents
        self.service_url = service_url
        self.knowledge_mode = knowledge_mode


class TaskScheduler:

    def __init__(self):
        self.unassigned_tasks = Queue()
        self.assigned_tasks = set()
        self.services = set()
        self.keep_running = False
        self.kb_location = "http://192.168.5.26:8001"

    def stop(self):
        self.keep_running = False

    def add_task(self, task: Task):
        self.unassigned_tasks.put(task)
        self.services.add(task.service_url)

    def solve_tasks(self):
        logger.debug("TaskScheduler::solve_tasks.1")
        self.keep_running = True
        while self.keep_running is True:
            logger.debug("TaskScheduler::solve_tasks.loop")
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

    def is_service_ready(self, service_url: str, agents: list) -> bool:
        logger.debug("TaskScheduler::is_service_ready(" + service_url + ", " + str(agents) + ")")
        s = ServerProxy("http://" + service_url + ":8000", allow_none=True)
        try:
            ready = s.is_ready(agents)
            logger.debug("TaskScheduler::is_service_ready.after_call")
            return ready
        except ConnectionRefusedError:
            logger.debug("TaskScheduler::is_service_ready.ConnectionRefusedError")
            return False

    def solve_task(self, task: Task):
        logger.debug("TaskScheduler::solve_task.starting at" +str(task.service_url)+" with task mode "+str(task.knowledge_mode))
        s = ServerProxy("http://" + task.service_url + ":8000", allow_none=True)
        knowledge_info = {
            "mode": task.knowledge_mode,
            "kb_location": self.kb_location
        }
        try:
            s.start_service(task.problem_definition, task.service_configuration, task.agents, knowledge_info)
            if s.wait_for_service() is False:
                self.unassigned_tasks.put(task)  # put task back into queue
            logger.debug("TaskScheduler::solve_task.finished")
        except ConnectionRefusedError:
            pass
