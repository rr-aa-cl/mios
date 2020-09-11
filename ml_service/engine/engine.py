import time
import datetime
import logging
from threading import Thread
from queue import Queue
from copy import deepcopy
import uuid
from mongodb_client.mongodb_client import MongoDBClient
from problem_definition.problem_definition import ProblemDefinition
from engine.task_result import TaskResult
from utils.exception import *
from utils.ws_client import *


logger = logging.getLogger("ml_service")


class Trial:
    def __init__(self, task_context: dict, reset_instructions: list, theta: dict):
        self.task_context = task_context
        self.reset_instructions = reset_instructions
        self.theta = theta
        self.task_result = TaskResult()

        self.t_0 = None
        self.t_1 = None
        self.t_delta = None

        self.task_uuid = "INVALID"
        self.trial_uuid = "INVALID"

        self.trial_number = 0

    def is_valid(self):
        if "name" not in self.task_context:
            logger.error("Task context has no name.")
            return False
        return True


class Engine:
    def __init__(self, agents: set = set()):
        logger.debug("Engine.__init__(" + str(agents) + ")")
        self.agents = agents
        self.free_agents = agents
        self.queued_trials = Queue()
        self.completed_trials = dict()

        self.database_client = MongoDBClient()
        self.database_results_collection = None
        self.database_results_id = None

        self.problem_definition = None

        self.keep_running = False
        self.max_trial_repeats = 3

        self.cnt_trial = 0

    def initialize(self, problem_definition: ProblemDefinition):
        self.initialize_results(problem_definition)

    def add_agent(self, agent: str):
        logger.debug("Engine.add_agent(" + str(agent) + ")")
        self.agents.add(agent)

    def remove_agent(self, agent: str):
        logger.debug("Engine.remove_agent(" + str(agent) + ")")
        if agent in self.agents:
            self.agents.remove(agent)

    def stop(self):
        self.keep_running = False

    def push_trial(self, trial: Trial) -> str:
        logger.debug("Engine.push_trial()")
        if trial.is_valid() is False:
            return "INVALID"
        trial.trial_uuid = str(uuid.uuid4())
        self.queued_trials.put(deepcopy(trial))
        return trial.trial_uuid

    def wait_for_trial(self, trial_uuid: str, max_wait_time: float) -> Trial:
        logger.debug("Engine.wait_for_trial(" + trial_uuid + ", " + str(max_wait_time) + ")")
        t_0 = time.time()
        while trial_uuid not in self.completed_trials:
            if time.time() - t_0 > max_wait_time or self.keep_running is False:
                logger.error("Wait time for trial has been exceeded.")
                return Trial(dict(), [], dict())
            time.sleep(0.1)

        return self.completed_trials[trial_uuid]

    def initialize_results(self, problem_definition: ProblemDefinition):
        self.problem_definition = problem_definition
        meta_data = problem_definition.to_dict()
        meta_data["t_0"] = time.time()
        meta_data["date"] = str(datetime.datetime.now())
        self.database_results_collection = self.database_client.client.ml_results[problem_definition.task_type]
        self.database_results_id = self.database_results_collection.insert_one(
            {"meta": meta_data}).inserted_id

    def main_loop(self):
        logger.debug("Engine.main_loop()")
        self.cnt_trial = 1
        self.keep_running = True
        worker_threads = dict()
        for a in self.agents:
            worker_threads[a] = None

        while self.keep_running is True:
            trial = self.queued_trials.get()
            logger.debug("Engine.main_loop.for1: For trial_uuid: " + trial.trial_uuid)
            thread_started = False
            while self.keep_running is True and thread_started is False:
                for a in self.agents.copy():
                    if a not in self.free_agents:
                        logger.debug("Agent " + a + " not in self.free_agents")
                        time.sleep(1)
                        continue
                    if worker_threads[a] is not None and worker_threads[a].is_alive() is True:
                        logger.debug("Thread of agent " + a + " is alive")
                        time.sleep(1)
                        continue

                    logger.debug("Engine.main_loop().is_busy(" + a + ")")
                    response = call_method(a, 12000, "is_busy")
                    if response is None:
                        logger.debug("is_busy on agent " + a + ": response is None")
                        time.sleep(1)
                        continue
                    if response["result"]["busy"] is True:
                        logger.debug("is_busy on agent " + a + ": is busy")
                        time.sleep(1)
                        continue

                    self.free_agents.remove(a)
                    worker_threads[a] = Thread(target=self._worker_loop, args=(a, trial,))
                    worker_threads[a].start()
                    thread_started = True

            time.sleep(0.1)

        for a in self.agents:
            if worker_threads[a] is not None:
                worker_threads[a].join(1000)

    def _worker_loop(self, agent: str, trial: Trial):
        logger.debug("Engine._worker_loop(" + agent + ", " + trial.trial_uuid + ")")
        if trial.is_valid() is False:
            raise ProblemDefinitionError

        result = self._execute_task(agent, trial)
        if result is False:
            logger.warning("Could not execute task for agent " + agent + ". Trial will be re-inserted into queue.")
            self.queued_trials.put(trial)
        else:
            self.queued_trials.task_done()
            self.completed_trials[trial.trial_uuid] = trial

        self._reset_task(agent, trial)
        self.free_agents.add(agent)

    def _execute_task(self, agent: str, trial: Trial) -> bool:
        logger.debug("Engine._execute_task(" + agent + ")")
        logger.debug("Engine::_execute_task.task_context: " + str(trial.task_context))
        cnt_repeat = -1
        while cnt_repeat < self.max_trial_repeats and self.keep_running is True:
            logger.debug("Engine::_execute_task.loop")
            cnt_repeat += 1
            result, task_uuid = self._start_task(agent, trial.task_context)
            if result is False:
                return False

            trial.t_0 = time.time()
            result, trial.task_result = self._wait_for_task(agent, task_uuid)
            if result is False:
                return False
            if "TaskError" in trial.task_result.errors:
                logger.error("Received an task error, service will terminate.")
                self.stop()
                return False
            if "RealTimeError" in trial.task_result.errors:
                logger.warning("Received a realtime error, trial will be repeated.")
                time.sleep(1)
                continue
            if "UserStopped" in trial.task_result.errors:
                logger.warning("Received a user stop error, trial will be repeated.")
                time.sleep(1)
                continue

            trial.t_1 = time.time()
            trial.t_delta = trial.t_1 - trial.t_0
            trial.trial_number = self.cnt_trial
            self.cnt_trial += 1
            trial.task_result.final_cost = self.problem_definition.calculate_cost(trial.task_result)
            self.write_task_result(trial)
            break
        return cnt_repeat < self.max_trial_repeats and self.keep_running is True

    def _reset_task(self, agent: str, trial: Trial):
        logger.debug("Engine::_reset_task()")
        for i in trial.reset_instructions:
            logger.debug("Engine::_reset_task.instructions: " + str(i["parameters"]))
            instruction_done = False
            while self.keep_running is True and instruction_done is False:
                logger.debug("Engine::_reset_task.loop")
                if i["method"] == "start_task":
                    result, task_uuid = self._start_task(agent, i["parameters"])
                    if result is False:
                        logger.debug("Reset task could not be started.")
                        logger.debug(result)
                        time.sleep(1)
                        continue

                    result, trial.task_result = self._wait_for_task(agent, task_uuid)
                    if result is False or trial.task_result.success is False:
                        logger.debug("Could not wait for reset_task")
                        logger.debug(result)
                        time.sleep(1)
                        continue
                else:
                    response = call_method(agent, 12000, i["method"], i["parameters"])
                    if response is None:
                        logger.debug(response)
                        time.sleep(1)
                        continue

                instruction_done = True

        logger.debug("Engine::_reset_task.end")

    def _start_task(self, agent: str, task_context: dict) -> (bool, str):
        task_uuid = "INVALID"
        task_name = task_context["name"]
        logger.info("Executing task " + task_name + " on agent " + agent + ".")
        logger.debug("Task context: " + str(task_context))
        response = start_task(agent, task_name, task_context, True)
        if response is None:
            logger.warning("Agent " + agent + " is not responding.")
            time.sleep(1)
            return False, task_uuid

        if "result" not in response or "result" not in response["result"]:
            logger.warning("I received no proper response from agent " + agent + ".")
            logger.debug("Response was: " + str(response))
            time.sleep(1)
            return False, task_uuid

        if response["result"]["result"] is False:
            logger.warning("The task " + task_name + " could not be started on agent " + agent + ".")
            logger.warning("Received message: " + response["result"]["error"])
            time.sleep(1)
            return False, task_uuid

        if "task_uuid" not in response["result"] or response["result"]["task_uuid"] == "INVALID":
            print("Response from agent " + agent + " did not contain a valid task uuid.")
            time.sleep(1)
            return False, task_uuid

        task_uuid = response["result"]["task_uuid"]
        return True, task_uuid

    def _wait_for_task(self, agent: str, task_uuid: str) -> (bool, TaskResult):
        task_result = TaskResult()
        response = wait_for_task(agent, task_uuid)
        logger.debug("Engine._wait_for_task.response: " + str(response))
        if response is None:
            logger.warning("Agent " + agent + " is not responding.")
            time.sleep(1)
            return False, task_result

        if "result" not in response or "result" not in response["result"] or "task_result" not in response["result"]:
            logger.warning("I received no proper response from agent " + agent + ".")
            logger.debug("Response was: " + str(response))
            time.sleep(1)
            return False, task_result

        if response["result"]["result"] is False:
            logger.warning("The task " + task_uuid + " was not properly executed on " + agent + ".")
            logger.warning("Received message: " + response["result"]["error"])
            time.sleep(1)
            return False, task_result

        if task_result.calculate(response["result"]["task_result"]) is False:
            time.sleep(1)
            return False, task_result

        return True, task_result

    def write_task_result(self, trial: Trial):
        data = {
            "theta": trial.theta,
            "cost": trial.task_result.final_cost,
            "success": trial.task_result.success,
            "t_0": trial.t_0,
            "t_1": trial.t_1,
            "t_delta": trial.t_delta
        }
        logger.debug("Engine::write_task_result.data: " + str(data))
        self.database_results_collection.update_one({'_id': self.database_results_id},
                                                    {'$set': {'n' + str(trial.trial_number): data}}, upsert=False)
