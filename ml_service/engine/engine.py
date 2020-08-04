import time
import logging
from threading import Thread
from queue import Queue
from multiprocessing.pool import ThreadPool
from copy import deepcopy
import uuid
from utils.exception import *
from utils.udp_client import *


logger = logging.getLogger("ml_service")


class TaskResult:
    def __init__(self):
        self.cost = None
        self.success = None
        self.t_0 = 0
        self.t_1 = 0

    def from_dict(self, result: dict) -> bool:
        if "cost" not in result:
            logger.error("No cost in task result.")
            return False

        self.cost = result["cost"]
        self.success = result["success"]
        return True


class Trial:
    def __init__(self, task_context: dict, reset_instructions: list):
        self.task_context = task_context
        self.reset_instructions = reset_instructions
        self.task_result = TaskResult()

        self.task_uuid = "INVALID"

        self.assigned = False

    def is_valid(self):
        return True


class Engine:
    def __init__(self, agents: set=set()):
        self.logger.debug("LoadBalancer.__init__(" + str(agents) + ")")
        self.agents = agents
        self.free_agents = agents
        self.logger = logging.getLogger("ml_service")
        self.active_trials = dict()
        self.completed_trials = dict()

        self.keep_running = False
        self.max_trial_repeats = 3

    def add_agent(self, agent: str):
        self.logger.debug("LoadBalancer.add_agent(" + str(agent) + ")")
        self.agents.add(agent)

    def remove_agent(self, agent: str):
        self.logger.debug("LoadBalancer.remove_agent(" + str(agent) + ")")
        if agent in self.agents:
            self.agents.remove(agent)

    def push_trial(self, trial: Trial):
        trial_uuid = str(uuid.uuid4())
        self.active_trials[trial_uuid] = deepcopy(trial)
        return trial_uuid

    def main_loop(self):
        worker_threads = dict()
        for a in self.agents:
            worker_threads[a] = None

        while self.keep_running is True:
            for uuid, trial in self.active_trials.items():
                if trial.assigned is True:
                    continue
                thread_started = False
                while self.keep_running is True and thread_started is False:
                    for a in self.agents:
                        if a not in self.free_agents:
                            continue
                        if worker_threads[a].is_alive() is True:
                            continue

                        response = call_method(a, 12002, "is_busy")
                        if response is None:
                            continue
                        if response["result"]["busy"] is True:
                            continue

                        trial.assigned = True
                        self.free_agents.remove(a)
                        worker_threads[a] = Thread(target=self._worker_loop, args=(a, uuid, trial,))
                        worker_threads[a].start()
                        thread_started = True
                        break

            time.sleep(0.1)

        for a in self.agents:
            if worker_threads[a] is not None:
                worker_threads[a].join(1000)

    def _worker_loop(self, agent, trial_uuid: str, trial: Trial):
        if trial.is_valid() is False:
            raise ProblemDefinitionError

        result = self._execute_task(agent, trial)
        if result is False:
            self.logger.warning("Could not execute task for agent " + agent + ". Trial will be re-inserted into queue.")
        else:
            self.active_trials.pop(trial_uuid)
            self.completed_trials[trial_uuid] = trial

        trial.assigned = False
        if self._reset_task(agent, trial) is False:
            raise Exception

        self.free_agents.add(agent)

    def _execute_task(self, agent: str, trial: Trial) -> bool:
        cnt_repeat = -1
        while cnt_repeat < self.max_trial_repeats and self.keep_running is True:
            cnt_repeat += 1
            result, task_uuid = self._start_task(agent, trial.task_context)
            trial.task_result.t_0 = time.time()
            if result is False:
                return False

            result, trial.task_result = self._wait_for_task(agent, task_uuid)
            trial.task_result.t_1 = time.time()
            if result is False:
                return False

            errors = trial.task_result["error"]
            if "realtime_error" in errors:
                time.sleep(1)
                continue

            break
        return cnt_repeat < self.max_trial_repeats

    def _reset_task(self, agent: str, trial: Trial) -> bool:
        for i in trial.reset_instructions:
            if i["method"] == "start_task":
                result, task_uuid = self._start_task(agent, trial.task_context)
                if result is False:
                    return False

                result, trial.task_result = self._wait_for_task(agent, task_uuid)
                if result is False or trial.task_result.success is False:
                    return False
            else:
                call_method(agent, 12002, i["method"], i["parameters"])

    def _start_task(self, agent: str, task_context: dict) -> (bool, str):
        cnt_repeat = -1
        task_uuid = "INVALID"
        while cnt_repeat < self.max_trial_repeats and self.keep_running is True:
            cnt_repeat += 1
            task_name = task_context["name"]
            self.logger.info("Executing task " + task_name + " on agent " + agent + ".")
            response = start_task(agent, task_name, task_context, True)
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

    def _wait_for_task(self, agent: str, task_uuid: str) -> (bool, TaskResult):
        cnt_repeat = -1
        task_result = TaskResult()
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
            if task_result.from_dict(response["result"]["task_result"]) is False:
                time.sleep(1)
                continue
            break

        return cnt_repeat < self.max_trial_repeats
