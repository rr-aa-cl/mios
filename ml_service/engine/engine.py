import time
import logging
from threading import Thread
from queue import Queue
from multiprocessing.pool import ThreadPool
from copy import deepcopy
from utils.exception import *

from utils.udp_client import *


class Engine:
    def __init__(self, agents: set=set()):
        self.logger.debug("LoadBalancer.__init__(" + str(agents) + ")")
        self.agents = agents
        self.logger = logging.getLogger("ml_service")
        self.job_queue = Queue()
        self.task_results = Queue()

        self.keep_running = False
        self.max_trial_repeats = 3

    def add_agent(self, agent: str):
        self.logger.debug("LoadBalancer.add_agent(" + str(agent) + ")")
        self.agents.add(agent)

    def remove_agent(self, agent: str):
        self.logger.debug("LoadBalancer.remove_agent(" + str(agent) + ")")
        if agent in self.agents:
            self.agents.remove(agent)

    def push_task(self, task_context):
        self.job_queue.put(deepcopy(task_context))

    def main_loop(self):
        worker_threads = dict()
        for a in self.agents:
            worker_threads[a] = None

        while self.keep_running is True:
            job = self.job_queue.get()

            thread_started = False
            while self.keep_running is True and thread_started is False:
                for a in self.agents:
                    if worker_threads[a].is_alive() is True:
                        continue

                    response = call_method(a, 12002, "is_busy")
                    if response is None:
                        continue
                    if response["result"]["busy"] is True:
                        continue

                    worker_threads[a] = Thread(target=self._worker_loop, args=(a, job,))
                    worker_threads[a].start()
                    thread_started = True
                    break

        for a in self.agents:
            if worker_threads[a] is not None:
                worker_threads[a].join(1000)

    def _worker_loop(self, agent, job):
        if "task" not in job:
            self.logger.critical("No task context in job!")
            raise ProblemDefinitionError

        if "reset_instructions" not in job["task"]:
            self.logger.exception("Problem definition does not contain reset instructions, aborting...")
            raise ProblemDefinitionError

        result, task_result = self._execute_task(agent, job)
        if result is False:
            self.logger.warning("Could not execute task for agent " + agent + ". Job will be re-inserted into queue.")
            self.job_queue.task_done()
            self.job_queue.put(deepcopy(job))
        else:
            self.task_results.put(deepcopy(task_result))
            self.job_queue.task_done()

    def _execute_task(self, agent: str, job: dict) -> (bool, dict):
        cnt_repeat = -1
        task_result = None
        while cnt_repeat < self.max_trial_repeats and self.keep_running is True:
            cnt_repeat += 1
            result, task_uuid = self._start_task(agent, job)
            if result is False:
                return False, None

            result, task_result = self._wait_for_task(agent, task_uuid)
            task_result["task_uuid"] = task_uuid
            if result is False:
                return False, None

            errors = task_result["error"]
            if "realtime_error" in errors:
                time.sleep(1)
                continue

            break
        return cnt_repeat < self.max_trial_repeats, task_result

    def _start_task(self, agent: str, job: dict) -> (bool, str):
        cnt_repeat = -1
        task_uuid = "INVALID"
        while cnt_repeat < self.max_trial_repeats and self.keep_running is True:
            cnt_repeat += 1
            task_name = job["task"]["name"]
            job["meta"] = time.time()
            self.logger.info("Executing task " + task_name + " on agent " + agent + ".")
            response = start_task(agent, task_name, job["task"], True)
            if response is None:
                self.logger.warning("Agent " + agent + " is not responding.")
                time.sleep(1)
                continue
            if "result" not in response or "result" not in response["result"]:
                self.logger.warning("I received no proper response from agent " + agent + ".")
                self.logger.debug("Response was: " + str(response))
                time.sleep(1)
                continue
            if response["result"]["result"] is False:
                self.logger.warning("The task " + task_name + " could not be started on agent " + agent + ".")
                self.logger.warning("Received message: " + response["result"]["error"])
                time.sleep(1)
                continue
            if "task_uuid" not in response["result"] or response["result"]["task_uuid"] == "INVALID":
                print("Response from agent " + agent + " did not contain a valid task uuid.")
                time.sleep(1)
                continue

            task_uuid = response["result"]["task_uuid"]
            break

        return cnt_repeat < self.max_trial_repeats, task_uuid

    def _wait_for_task(self, agent: str, task_uuid: str) -> (bool, dict):
        cnt_repeat = -1
        task_result = None
        while cnt_repeat < self.max_trial_repeats and self.keep_running is True:
            cnt_repeat += 1
            response = wait_for_task(agent, task_uuid)
            if response is None:
                self.logger.warning("Agent " + agent + " is not responding.")
                time.sleep(1)
                continue
            if "result" not in response or "result" not in response["result"] or "task_result" not in response["result"]:
                self.logger.warning("I received no proper response from agent " + agent + ".")
                self.logger.debug("Response was: " + str(response))
                time.sleep(1)
                continue
            if response["result"]["result"] is False:
                self.logger.warning("The task " + task_uuid + " was not properly executed on " + agent + ".")
                self.logger.warning("Received message: " + response["result"]["error"])
                time.sleep(1)
                continue
            task_result = response["result"]["task_result"]
            break

        return cnt_repeat < self.max_trial_repeats, task_result
