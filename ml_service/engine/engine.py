import time
import datetime
import logging
import os
from threading import Thread
from threading import Lock
from threading import Event
from queue import Queue
from queue import Empty
from copy import deepcopy
import uuid
import numpy as np
from pymongo import timeout as mongo_timeout
from pymongo.write_concern import WriteConcern
from mongodb_client.mongodb_client import MongoDBClient
from problem_definition.problem_definition import ProblemDefinition
#from collective_manager.video_recorder import FFMpegWebcamRecorder
from engine.task_result import TaskResult
from utils.exception import *
from utils.ws_client import *
from utils.helper_functions import *
import redis
import json


logger = logging.getLogger("ml_service")


class Trial:
    def __init__(self, task_context: dict, reset_instructions: list, rescue_instructions:list, theta: dict, log: bool = True, external = False):
        self.task_context = task_context
        self.reset_instructions = reset_instructions
        self.rescue_instructions = rescue_instructions
        self.theta = theta
        self.task_result = TaskResult()

        self.t_0 = None
        self.t_1 = None
        self.t_delta = None

        self.task_uuid = "INVALID"
        self.trial_uuid = "INVALID"
        self.agent = "INVALID"

        self.trial_number = 0
        self.log = log

        self.external = external

    def to_dict(self):
        for key in self.theta.keys():
            self.theta[key] = float(self.theta[key])
        trial_dict = {
            "task_context": self.task_context,
            "reset_instructions": self.reset_instructions,
            "theta": self.theta,
            "task_result": self.task_result.to_dict(),
            "t_0": self.t_0,
            "t_1": self.t_1,
            "t_delta": self.t_delta,
            "task_uuid": self.task_uuid,
            "trial_uuid": self.trial_uuid,
            "agent": self.agent,
            "trial_number": self.trial_number,
            "log": self.log,
            "external": self.external
        }
        return trial_dict

    def is_valid(self):
        if "name" not in self.task_context:
            logger.error("Task context has no name.")
            return False
        return True


class Engine:
    def __init__(self, agents: set = None, mios_port=12000, mongo_port=27017):
        logger.debug("Engine.__init__(" + str(agents) + ") with mios-port:" + str(mios_port))
        if agents is None:
            agents = set()
        self.mios_port = mios_port
        self.mongo_port = mongo_port
        self.agents = set(agents)
        self.free_agents = set(agents)
        self.queued_trials = Queue()
        self.completed_trials = dict()
        # Redis is only an optional notification sink.  Keep it disabled by
        # default for a standalone robot deployment; enable it explicitly for
        # a collective-learning deployment with MIOS_ENABLE_REDIS=true.
        self.redisClient = None
        if os.getenv("MIOS_ENABLE_REDIS", "false").strip().lower() in {"1", "true", "yes", "on"}:
            try:
                self.redisClient = redis.Redis(
                        host="redis-master.global",
                        port=6379,
                        db=0,
                        decode_responses=True,
                        password="QqJ3JDqNjN",
                        socket_connect_timeout=2,
                        socket_timeout=2,
                     )
                self.redisClient.ping()
            except redis.RedisError as e:
                logger.error("Redis connection failed: " + str(e))
                self.redisClient = None
        self.database_client = MongoDBClient(port=self.mongo_port)
        self.log_client = MongoDBClient(
            os.getenv("MIOS_ML_LOG_MONGO_HOST", "localhost"),
            port=self.mongo_port,
        )
        self.database_results_collection = None
        self.database_results_id = None

        self.problem_definition = None
        self.meta_data = dict()

        self.keep_running = False
        self.stop_requested = Event()
        self.started = Event()
        self._dispatch_lock = Lock()
        self._stop_lock = Lock()
        self._owned_agents = set()
        self._cleanup_complete = Event()
        self._cleanup_complete.set()
        self.worker_threads = {}
        self.pause_execution = False
        self.max_trial_repeats = 3

        self.cnt_trial = 0
        self.cnt_pushed = 0
        self.cnt_completed = 0
        self.cnt_optimal = 0
        self.stop_condition = None

        self.x = np.empty((0, 0))
        self.y = np.empty((0,))

        self.lock_data = Lock()

        self.exploration_mode = False
        #self.camera_path =  os.getenv("cameraPath")
        #if self.camera_path is None:
        #    self.camera_path = "/dev/video4"
        #self.video_recorder = FFMpegWebcamRecorder(self.camera_path)
        self.skill_count=0

    def _get_log_timestamp(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
    

    def _get_trial_job_name(self, trial: Trial) -> str:
        job_name = trial.task_context["name"]
        for skill_name in trial.task_context.get("parameters", {}).get("skill_names", []):
            skill = trial.task_context.get("skills", {}).get(skill_name, {})
            objects = skill.get("skill", {}).get("objects", {})
            if "Insertable" in objects:
                return objects["Insertable"]
        return job_name

    def initialize(self, problem_definition: ProblemDefinition, exploration_mode: bool = False):
        self.x = np.empty((0, len(problem_definition.domain.limits)))
        self.exploration_mode = exploration_mode
        return self.initialize_results(problem_definition)
 
    def register_stop_condition(self, stop_condition):  # unused?
        self.stop_condition = stop_condition

    def add_agent(self, agent: str):
        logger.debug("Engine.add_agent(" + str(agent) + ")")
        self.agents.add(agent)

    def remove_agent(self, agent: str):
        logger.debug("Engine.remove_agent(" + str(agent) + ")")
        if agent in self.agents:
            self.agents.remove(agent)

    def stop(self):
        logger.info("Engine.stop() - received stop signal.")
        self.stop_requested.set()
        self.keep_running = False
        # Mutating requests already in flight must precede the Core stop. New
        # requests recheck the sticky latch while holding this same lock.
        if not self._stop_lock.acquire(timeout=2.5):
            logger.error("Another Core stop attempt is still pending.")
            return False
        try:
            if not self._dispatch_lock.acquire(timeout=2.5):
                logger.error("A Core dispatch is still pending; stop will follow its reply.")
                return False
            try:
                return self._stop_owned_agents()
            finally:
                self._dispatch_lock.release()
        finally:
            self._stop_lock.release()

    def _stop_owned_agents(self):
        success = True
        try:
            for agent in tuple(self._owned_agents):
                try:
                    response = stop_task(agent, raise_exception=False, recover=False,
                                         empty_queue=True, port=self.mios_port,
                                         timeout=5, open_timeout=2, close_timeout=0.2)
                    result = response.get("result") if isinstance(response, dict) else None
                    accepted = isinstance(result, dict) and result.get("result") is True
                except Exception:
                    logger.exception("Core stop request failed for agent %s", agent)
                    accepted = False
                if accepted:
                    self._owned_agents.discard(agent)
                else:
                    logger.error("Core did not acknowledge stopping agent %s; retry stop_service.", agent)
                    success = False
        finally:
            if not self._owned_agents:
                self._cleanup_complete.set()
        return success

    def _running(self):
        return self.keep_running and not self.stop_requested.is_set()

    def _dispatch_instruction(self, agent, method, parameters):
        with self._dispatch_lock:
            if not self._running():
                return None
            already_owned = agent in self._owned_agents
            self._owned_agents.add(agent)
            self._cleanup_complete.clear()
            response = call_method(agent, self.mios_port, method, parameters,
                                   timeout=100, open_timeout=2, close_timeout=0.2)
            result = response.get("result") if isinstance(response, dict) else None
            # This reply cannot resolve an earlier task whose acknowledgement
            # was lost; keep that ownership until task completion or Core stop.
            if not already_owned and isinstance(result, dict) and result.get("result") is True:
                self._owned_agents.discard(agent)
                if not self._owned_agents:
                    self._cleanup_complete.set()
        if self.stop_requested.is_set():
            self.stop()
            return None
        return response
    
    def pause(self):
        self.pause_execution = True

    def resume(self):
        self.pause_execution = False

    def push_trial(self, trial: Trial) -> str:
        #logger.debug("Engine.push_trial()")
        if self.stop_requested.is_set() or trial.is_valid() is False:
            return "INVALID"
        trial.trial_uuid = str(uuid.uuid4())
        self.cnt_pushed += 1
        self.queued_trials.put(deepcopy(trial))
        return trial.trial_uuid

    def wait_for_trial(self, trial_uuid: str, max_wait_time: float) -> Trial:
        deadline = time.monotonic() + max_wait_time
        while trial_uuid not in self.completed_trials:
            if not self._running():
                raise StopService(f"Learning stopped while waiting for trial {trial_uuid}.")
            if time.monotonic() >= deadline:
                message = (
                    f"Trial {trial_uuid} did not complete within {max_wait_time} seconds; "
                    "cancelling learning."
                )
                logger.error(message)
                # A timeout is not a completed trial. Cancel outstanding work
                # before the optimizer can consume a fabricated cost or queue
                # another candidate while this worker still owns the robot.
                self.stop()
                raise StopService(message)
            self.stop_requested.wait(0.05)

        self.cnt_completed += 1

        return self.completed_trials[trial_uuid]

    def initialize_results(self, problem_definition: ProblemDefinition):
        self.problem_definition = problem_definition
        self.meta_data = problem_definition.to_dict()
        self.meta_data["t_0"] = time.time()
        now = datetime.datetime.now()
        now.strftime("%Y-%m-%d_%H:%M:%S")
        self.meta_data["date"] = now.strftime("%Y-%m-%d_%H:%M:%S")
        self.database_results_collection = self.database_client.client.ml_results[problem_definition.skill_class]
        self.database_results_id = self.database_results_collection.insert_one(
            {"meta": self.meta_data}).inserted_id
        return self.database_results_id

    def is_learned(self) -> bool:
        if self.exploration_mode is True:
            #logger.debug("Engine.is_learned() -> exploration_mode=True")
            return False
        else:
            #logger.debug("Engine.is_learned()? "+str(self.cnt_optimal > self.problem_definition.cost_function.finish_thr))
            return self.cnt_optimal > self.problem_definition.cost_function.finish_thr  # finsih threshold states how often a optimal_thr was undercut to finish

    def main_loop(self):
        logger.debug("Engine.main_loop()")
        self.keep_running = not self.stop_requested.is_set()
        self.started.set()
        try:
            self._main_loop()
        except BaseException:
            self.stop()
            raise
        finally:
            # Do not let BaseService/Interface advertise idle while a worker
            # can still dispatch or an owned Core task has an unresolved stop.
            for worker in self.worker_threads.values():
                if worker is not None and worker.ident is not None:
                    worker.join()
            if self.stop_requested.is_set():
                self._cleanup_complete.wait()
            self.keep_running = False
            self.write_final_results()

    def _main_loop(self):
        self.cnt_trial = 1
        worker_threads = self.worker_threads
        for a in self.agents:
            worker_threads[a] = None

        logger.info("Setting up experiment.")
        for a in self.free_agents.copy():
            if not self._running():
                break
            worker_threads[a] = Thread(target=self._setup_worker, args=(a,))
            worker_threads[a].start()

        for worker in worker_threads.values():
            if worker is not None and worker.ident is not None:
                worker.join()

        logger.info("Setup procedure done.")

        # Keep each agent's log deadline across queued trials.
        next_assigned_agent_log = {}
        while self._running():
            try:
                #logger.debug("Engine::main_loop.get_trial")
                trial = self.queued_trials.get(timeout=0.1)
                # logger.debug("Engine::main_loop.new_trial: " + trial.trial_uuid)
            except Empty:
                # self.stop_requested.wait(0.1)
                continue
            # logger.debug("Engine.main_loop.while1: For trial_uuid: " + trial.trial_uuid)
            thread_started = False
            next_wait_log = 0.0
            while self._running() and thread_started is False:
                # logger.debug("Engine::main_loop.while2")
                if self.is_learned() is True:
                    logger.debug("Engine::main_loop.is_learned")
                    self.keep_running = False
                    continue
                now = time.monotonic()
                log_wait_state = now >= next_wait_log
                if log_wait_state:
                    next_wait_log = now + 5.0
                for a in self.agents.copy():
                    if a not in self.free_agents:
                        wait_log_time = time.monotonic()
                        if wait_log_time >= next_assigned_agent_log.get(a, wait_log_time):
                            logger.debug("Agent %s is still assigned to a trial worker; waiting.", a)
                            next_assigned_agent_log[a] = wait_log_time + 30.0
                        continue
                    if worker_threads[a] is not None and worker_threads[a].is_alive() is True:
                        if log_wait_state:
                            logger.debug("Agent %s is finishing worker cleanup; waiting.", a)
                        continue

                    # logger.debug("Engine.main_loop().is_busy(" + a + ")")
                    response = call_method(a, self.mios_port, "is_busy", timeout=5,
                                           open_timeout=2, close_timeout=0.2,
                                           cancel_event=self.stop_requested)
                    if response is None:
                        if log_wait_state:
                            logger.debug("is_busy on agent %s: response is None", a)
                        continue
                    if response["result"]["busy"] is True:
                        if log_wait_state:
                            logger.debug("is_busy on agent %s: is busy", a)
                        continue

                    if not self._running():
                        break

                    self.free_agents.remove(a)
                    trial.agent = a
                    worker = None
                    try:
                        worker = Thread(target=self._worker_loop, args=(a, trial,))
                        worker_threads[a] = worker
                        worker.start()
                    except BaseException:
                        # A worker that never started cannot run its finally
                        # block. Restore only that reservation; a started
                        # worker still owns its own release/queue accounting.
                        if worker is None or worker.ident is None:
                            worker_threads[a] = None
                            self.free_agents.add(a)
                            self.queued_trials.task_done()
                        raise
                    thread_started = True
                    break

                if not thread_started:
                    # Scan every agent before waiting, so an occupied worker
                    # cannot delay another free robot. Yield CPU while all
                    # agents are unavailable, and wake immediately on stop.
                    self.stop_requested.wait(0.1)

            if not thread_started:
                self.queued_trials.task_done()

            # self.stop_requested.wait(0.1)

        logger.debug("Engine::main_loop.after_loop")
        logger.debug("Engine::main_loop.last_line")

    def _setup_worker(self, agent):
        try:
            self.setup_experiment(agent)
        except Exception:
            logger.exception("Experiment setup failed for agent %s", agent)
            self.stop()

    def _worker_loop(self, agent: str, trial: Trial):
        logger.debug("Engine._worker_loop(" + agent + ", " + trial.trial_uuid + ")")
        try:
            self._run_trial(agent, trial)
        except Exception:
            logger.exception("Trial worker failed for agent %s", agent)
            self.stop()
        finally:
            self.free_agents.add(agent)
            self.queued_trials.task_done()
        logger.debug("Free agent " + agent)
        #self.video_recorder.stop_stream()

    def _run_trial(self, agent: str, trial: Trial):
        if not self._running():
            return
        if trial.is_valid() is False:
            raise ProblemDefinitionError
        trial.trial_number = self.cnt_trial
        self.cnt_trial += 1
        trial.t_0 = time.time()
        start_timestamp = self._get_log_timestamp()
        end_timestamp = start_timestamp
        job_name = self._get_trial_job_name(trial)
        doc = {
            "jobName" : job_name,
            "timestamp": start_timestamp,
            "step": "running/" + str(trial.trial_number),
            "message": "start trial"
        }
        self.log_client.write("collective_learning_system", "jobs_log", doc)
        # start video recording
        folder = str(self.problem_definition.tags[0]) + "/" +str(self.problem_definition.tags[1]) + "/"+str(self.problem_definition.skill_instance)
        filename = "n_"+str(trial.trial_number)
        # if not self.video_recorder.start_stream(
        #     output_folder="videos/"+folder,
        #     base_filename=filename,
        #     compressed=False,rotate=True,
        #     framerate="30",
        #     resolution="1920x1080",
        #     pixel_format="yuyv422"):
        #     logger.error("!!!!Cannot start video recording!!!!")
        #     pass

        for i in range(self.problem_definition.n_variations):
            if not self._running():
                return
            #print("Running variation " + str(i))
            self.problem_definition.apply_object_modifiers(trial.task_context)
            result, variation_result = self._execute_task(agent, trial)
            if self._running():
                if result is False:
                    logger.warning("Could not execute task for agent " + agent + ". Trial will be re-inserted into queue.")
                    self.queued_trials.put(trial)
                    self._reset_task(agent, trial)
                    return
            else:
                return

            theta = np.zeros((1, (len(self.problem_definition.domain.limits))))
            for j in range(len(self.problem_definition.domain.limits)):
                theta[0][j] = trial.theta[self.problem_definition.domain.vector_mapping[j]]

            if i == 0:
                trial.task_result = variation_result
            else:
                trial.task_result.add_variation(variation_result.q_metric)

            trial.t_1 = time.time()
            end_timestamp = self._get_log_timestamp()
            trial.t_delta = trial.t_1 - trial.t_0
            #print(trial.trial_number)

            self.lock_data.acquire()
            if trial.task_result.q_metric.final_cost < 1:
                self.x = np.append(self.x, theta, axis=0)
                self.y = np.append(self.y, trial.task_result.q_metric.final_cost)
            self.lock_data.release()
            self._reset_task(agent, trial)
            if not self._running():
                return
            
            if self.problem_definition.variate_only_success is True and trial.task_result.q_metric.success is False:
                #logger.debug("ENGINE: do not variate")
                break
            logger.debug("ENGINE:"+ str(i+1)+ ". variation done. Do "+str(self.problem_definition.n_variations)+" in total. ")

        #self.video_recorder.stop_stream()
        #logger.debug("Cost: " + str(trial.task_result.q_metric.final_cost))
        #logger.debug("FINISHED trial " + str(self.cnt_trial) + " with uuid " + trial.trial_uuid)
        if trial.task_result.q_metric.optimal is True:
            logger.debug("Engine::_worker_loop.is_optimal")
            self.cnt_optimal += 1

        trial.task_result.q_metric.heuristic = trial.task_result.q_metric.heuristic * (1 - trial.task_result.q_metric.success_rate)
        if trial.log is True:
            self.write_task_result(trial)
        else:
            # Even opt-out trials have transient dispatch evidence. Discard it
            # only after insertion and reset finish; retain it on interruption.
            self._write_results_update({"$unset": {self._pending_trial_path(trial): ""}})
        #logger.debug("Engine::_worker_loop.trial_done")
        cost = str(variation_result.q_metric.final_cost) if variation_result is not None else "None"
        logger.debug(f"\n#################################\n ENGINE: success {str(trial.task_result.q_metric.success)} on trial {str(trial.trial_number)}\n"
            f"ENGINE: Cost: {cost} \n#################################\n")
        self.completed_trials[trial.trial_uuid] = deepcopy(trial)
        
        doc = {
            "jobName" : job_name,
            "timestamp": end_timestamp,
            "step": "running/" + str(trial.trial_number),
            "message": "finish trial with result: " + str(trial.task_result.q_metric.success)
        }
        self.log_client.write("collective_learning_system", "jobs_log", doc)
        doc = {
            "jobName" : job_name,
            "trial_no": trial.trial_number,
            "result": trial.task_result.q_metric.success,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "theta": trial.theta if trial.task_result.q_metric.success is True else ""
        }
        self.log_client.write("collective_learning_system", "jobs_results", doc)

        if self.redisClient is not None:
            try: 
                self.redisClient.lpush("ml_result", json.dumps({"arm_label": trial.agent, "trial_count": trial.trial_number, "is_succeed": trial.task_result.q_metric.success}))
            except redis.RedisError as e:
                logger.error("Redis push data failed: " + str(e)) 

    def _execute_task(self, agent: str, trial: Trial) -> (bool, TaskResult):
        logger.debug("Engine._execute_task(" + agent + ") with trial " + trial.trial_uuid)
        # logger.debug("Engine::_execute_task.task_context: " + str(trial.task_context))
        cnt_repeat = -1
        variation_result = None
        while cnt_repeat < self.max_trial_repeats and self._running():
            logger.debug("Engine::_execute_task.loop")
            cnt_repeat += 1
            for skill_name in trial.task_context["skills"].keys():

                trial.task_context["skills"][skill_name]["skill"] = udpate_dict(trial.task_context["skills"][skill_name]["skill"], self.problem_definition.add_skill_info)  # ["log_name"] = is log_data, log_name meta etc realy in trial.task_context??
                if "log_name" in self.problem_definition.add_skill_info:
                    trial.task_context["skills"][skill_name]["skill"]["log_name"]+= "n"+str(trial.trial_number)+"/learning"
                trial.task_context["skills"][skill_name]["skill"]["meta"] = {
                        "description":"Execution of a trial as part of the learning process.",
                    }
            #print(str(trial.task_context))
            result, task_uuid = self._start_task(agent, trial.task_context, trial=trial)
            if result is False:
                logger.error("Result was False after start_task")
                return False, None
            trial.task_uuid = task_uuid
            result, variation_result = self._wait_for_task(agent, task_uuid, trial=trial)
            if result is False:
                logger.error("Result was False after wait_for_task")
                return False, None
            if any(error in variation_result.errors
                   for error in ("TaskError", "RealTimeError", "UserStopped")):
                logger.error("Core task %s on agent %s reported %s; cancelling learning.",
                             task_uuid, agent, variation_result.errors)
                self.stop()
                return False, None
            variation_result.q_metric = self.problem_definition.calculate_cost(variation_result)
            #print(variation_result.q_metric.final_cost)
            break
        #logger.debug("Engine::_execute_task.end")
        return cnt_repeat < self.max_trial_repeats and self._running(), variation_result

    def _instruction_preconditions_met(self, agent, instruction, phase):
        preconditions = instruction.get("preconditions", {})
        if preconditions == {}:
            return True
        if not isinstance(preconditions, dict):
            logger.error("Invalid %s preconditions for agent %s; cancelling learning.", phase, agent)
            self.stop()
            return False
        response = call_method(agent, self.mios_port, "get_state", timeout=5,
                               open_timeout=2, close_timeout=0.2,
                               cancel_event=self.stop_requested)
        if not self._running():
            return False
        state = response.get("result") if isinstance(response, dict) else None
        if (not isinstance(state, dict)
                or state.get("result") is not True
                or state.get("error") not in (None, "")
                or state.get("error_message") not in (None, "")
                or state.get("status") not in ("Idle", "Move")
                or any(key not in state for key in preconditions)):
            logger.error("Cannot confirm %s preconditions for agent %s; cancelling learning. State: %r",
                         phase, agent, response)
            self.stop()
            return False
        if any(state[key] != expected for key, expected in preconditions.items()):
            logger.warning("%s preconditions do not match on agent %s; skipping instruction.", phase, agent)
            return False
        return True

    def _reset_task(self, agent: str, trial: Trial):
        logger.debug("Engine::_reset_task()")
        for i in trial.reset_instructions:
            if not self._running():
                return
            #logger.debug("Engine::_reset_task.instructions: " + str(i["parameters"]))
            instruction_done = False
            while not instruction_done and self._running():
                #logger.debug("Engine::_reset_task.loop")
                # append meta information to skill context
                for skill_name in i["parameters"]["skills"].keys():
                    i["parameters"]["skills"][skill_name]["skill"] = udpate_dict(i["parameters"]["skills"][skill_name]["skill"], self.problem_definition.add_skill_info)
                    if "log_name" in self.problem_definition.add_skill_info:
                        i["parameters"]["skills"][skill_name]["skill"]["log_name"] += "n"+str(trial.trial_number)+"/reset_trial"
                        i["parameters"]["skills"][skill_name]["skill"]["meta"] = {
                            "description":"Resetting the trial to initial state"
                        }
                if not self._instruction_preconditions_met(agent, i, "Reset"):
                    break
                if i["method"] == "start_task":
                    result, task_uuid = self._start_task(agent, i["parameters"])
                    if result is False:
                        logger.debug("Reset task could not be started.")
                        logger.debug(result)
                        self.stop_requested.wait(1)
                        continue

                    result, task_result = self._wait_for_task(agent, task_uuid)
                    if not self._running():
                        return
                    if result is False or task_result.q_metric.success is False:
                        logger.debug("Could not wait for reset_task. do rescue...")
                        logger.debug(result)
                        self.stop_requested.wait(1)
                        self._rescue_task(agent, trial)
                        continue
                else:
                    response = self._dispatch_instruction(agent, i["method"], i["parameters"])
                    if response is None:
                        logger.debug(response)
                        self.stop_requested.wait(1)
                        continue

                instruction_done = True
        #logger.debug("Engine::_reset_task.end")

    def _rescue_task(self,agent:str, trial:Trial):
        logger.debug("Engine::_rescue_task() - try this move once")
        for i in trial.rescue_instructions:
            if not self._running():
                return
            for skill_name in i["parameters"]["skills"].keys():
                i["parameters"]["skills"][skill_name]["skill"] = udpate_dict(i["parameters"]["skills"][skill_name]["skill"], self.problem_definition.add_skill_info)
                if "log_name" in self.problem_definition.add_skill_info:
                    i["parameters"]["skills"][skill_name]["skill"]["log_name"] += "n"+str(trial.trial_number)+"/reset_trial"
                    i["parameters"]["skills"][skill_name]["skill"]["meta"] = {
                        "description":"Resetting the trial to initial state didn\'t work. Try to move away from stuck position"
                    }
            if not self._instruction_preconditions_met(agent, i, "Rescue"):
                continue
            if i["method"] == "start_task":
                result, task_uuid = self._start_task(agent, i["parameters"])
                if result is False:
                    logger.debug("Rescue task could not be started.")
                    logger.debug(result)
                    self.stop_requested.wait(1)
                    continue

                result, task_result = self._wait_for_task(agent, task_uuid)
                if result is False or task_result.q_metric.success is False:
                    logger.debug("Could not wait for rescue_task.")
                    logger.debug(result)
                    self.stop_requested.wait(1)
                    continue
            else:
                response = self._dispatch_instruction(agent, i["method"], i["parameters"])
                if response is None:
                    logger.debug(response)
                    self.stop_requested.wait(1)
                    continue

    def _start_task(self, agent: str, task_context: dict, *, trial=None) -> (bool, str):
        task_uuid = "INVALID"
        if not self._running():
            return False, task_uuid
        task_name = task_context["name"]
        for skill_name in task_context["skills"].keys():
                if "log_name" in task_context["skills"][skill_name]["skill"]:
                    task_context["skills"][skill_name]["skill"]["log_name"] += "_"+skill_name+"-"+str(self.skill_count)
                    task_context["skills"][skill_name]["skill"]["meta"]["context"] = copy.deepcopy(task_context["skills"][skill_name])
                    task_context["skills"][skill_name]["skill"]["meta"]["time"] = time.time()
                    task_context["skills"][skill_name]["skill"]["meta"]["tags"] = self.problem_definition.tags
        while self.pause_execution and self._running():
            self.stop_requested.wait(0.05)
        logger.info("_start_task::Executing task " + str(task_name) + " on agent " + str(agent) + ".")
        # logger.debug("Task context: " + str(task_context))
        dispatched = False
        with self._dispatch_lock:
            if not self._running():
                return False, task_uuid
            if trial is not None:
                self._record_pending_trial(agent, trial, task_context)
            # A stop can set the latch during the database write without
            # acquiring this lock. Skip dispatch, then retry stop outside the
            # lock if its earlier lock acquisition timed out during the save.
            if self._running():
                self._owned_agents.add(agent)
                self._cleanup_complete.clear()
                dispatched = True
                response = start_task(agent, task_name, task_context, True, port=self.mios_port,
                                      timeout=5, open_timeout=2, close_timeout=0.2)
        if not self._running():
            self.stop()
        if not dispatched:
            return False, task_uuid
        if trial is not None:
            result = response.get("result") if isinstance(response, dict) else None
            self._update_pending_trial(trial,
                dispatch_state="start_reply_missing" if response is None else "start_reply_received",
                start_reply_at_utc=self._get_log_timestamp(), start_response=response,
                task_uuid=result.get("task_uuid") if isinstance(result, dict) else None)
        if not self._running():
            return False, task_uuid
        result = response.get("result") if isinstance(response, dict) else None
        accepted = (isinstance(result, dict) and result.get("result") is True
                    and result.get("error") in (None, "")
                    and result.get("error_message") in (None, ""))
        reply_uuid = result.get("task_uuid") if isinstance(result, dict) else None
        if (not accepted or not isinstance(reply_uuid, str)
                or not reply_uuid.strip() or reply_uuid == "INVALID"):
            # A missing acknowledgement may still mean Core queued the task.
            # Never turn this into reset/rescue motion or another start request.
            logger.error("Core did not confirm starting task %s on agent %s; "
                         "cancelling learning. Response: %r", task_name, agent, response)
            self.stop()
            return False, task_uuid

        task_uuid = reply_uuid
        logger.debug("Core accepted task %s on agent %s with UUID %s.", task_name, agent, task_uuid)
        self.skill_count+=1
        return True, task_uuid

    def _wait_for_task(self, agent: str, task_uuid: str, *, trial=None) -> (bool, TaskResult):
        task_result = TaskResult()
        logger.debug("Waiting for Core task %s on agent %s.", task_uuid, agent)
        response = wait_for_task(agent, task_uuid, port=self.mios_port,
                                 open_timeout=2, close_timeout=0.2,
                                 cancel_event=self.stop_requested)
        # logger.debug("Engine._wait_for_task.response: " + str(response))
        if response is None and self._running():
            logger.error(
                "Lost Core response while waiting for task %s on agent %s; "
                "completion is unknown, cancelling learning.", task_uuid, agent)
            # The task may still be running. Request cancellation instead of
            # dispatching reset/rescue motions after an unconfirmed result.
            self.stop()
        if trial is not None:
            self._update_pending_trial(trial,
                dispatch_state="completion_reply_missing" if response is None else "completion_reply_received",
                completion_reply_at_utc=self._get_log_timestamp(), completion_response=response)
        if not self._running():
            return False, task_result

        result = response.get("result") if isinstance(response, dict) else None
        completion = result.get("task_result") if isinstance(result, dict) else None
        valid = (isinstance(result, dict) and result.get("result") is True
                 and result.get("error") in (None, "")
                 and result.get("error_message") in (None, "")
                 and isinstance(completion, dict)
                 and type(completion.get("success")) is bool
                 and isinstance(completion.get("error"), list)
                 and all(isinstance(error, str) for error in completion["error"])
                 and isinstance(completion.get("skill_results"), dict)
                 and completion.get("exception", False) is False
                 and completion.get("external_stop", False) is False)
        if valid:
            try:
                valid = task_result.calculate(completion) is True
            except (AttributeError, KeyError, TypeError, ValueError):
                valid = False
        if not valid:
            logger.error("Core did not confirm a usable completion for task %s on agent %s; "
                         "cancelling learning. Response: %r", task_uuid, agent, response)
            self.stop()
            return False, task_result

        # Setup/reset/rescue also use this method directly. A physical task
        # fault must cancel those phases before their retry loops can run.
        if any(error in task_result.errors
               for error in ("TaskError", "RealTimeError", "UserStopped")):
            logger.error("Core task %s on agent %s reported %s; cancelling learning.",
                         task_uuid, agent, task_result.errors)
            self.stop()
            return False, task_result

        with self._dispatch_lock:
            self._owned_agents.discard(agent)
            if not self._owned_agents:
                self._cleanup_complete.set()

        #logger.debug("Engine::_wait_for_task.end")
        return True, task_result

    def setup_experiment(self, agent):
        logger.debug("Engine::_reset_task()")
        for i in self.problem_definition.setup_instructions:
            if not self._running():
                return
            logger.debug("Engine::setup_experiment.instructions: " + str(i["parameters"]))
            for skill_name in i["parameters"]["skills"]:
                i["parameters"]["skills"][skill_name]["skill"] = udpate_dict(i["parameters"]["skills"][skill_name]["skill"], self.problem_definition.add_skill_info)
                if "log_name" in self.problem_definition.add_skill_info:
                    i["parameters"]["skills"][skill_name]["skill"]["log_name"] += "setup_experiment"
                i["parameters"]["skills"][skill_name]["skill"]["meta"] = {
                        "description": "Setting up the experiment to initial state."
                    }
            instruction_done = False
            while not instruction_done and self._running():
                logger.debug("Engine::_reset_task.loop")
                if i["method"] == "start_task":
                    result, task_uuid = self._start_task(agent, i["parameters"])
                    if result is False:
                        logger.debug("Setup experiment could not be started.")
                        logger.debug(result)
                        self.stop_requested.wait(1)
                        continue

                    result, task_result = self._wait_for_task(agent, task_uuid)
                    if result is False or task_result.q_metric.success is False:
                        logger.debug("Could not wait for setup_experiment")
                        logger.debug(result)
                        self.stop_requested.wait(1)
                        continue
                else:
                    response = self._dispatch_instruction(agent, i["method"], i["parameters"])
                    if response is None:
                        logger.debug(response)
                        self.stop_requested.wait(1)
                        continue

                instruction_done = True

        #logger.debug("Engine::setup_experiment.end")

    def write_final_results(self):
        data = {
            "time": time.time() - self.meta_data["t_0"],
            "n_trials": self.cnt_trial - 1
        }
        self.database_results_collection.update_one({"_id": self.database_results_id},
                                                    {"$set": {"final_results": data}}, upsert=False)

    @staticmethod
    def _pending_trial_path(trial):
        key = trial.trial_uuid
        if not isinstance(key, str) or not key or key == "INVALID" or "." in key or "$" in key:
            raise RuntimeError("Cannot audit a trial without a valid trial UUID.")
        return "pending_trials." + key

    def _write_results_update(self, update):
        """Require an acknowledged, journaled write to the existing run record."""
        if self.database_results_collection is None or self.database_results_id is None:
            raise RuntimeError("Cannot persist trial evidence before the results database is initialized.")
        # Audit I/O must not hold dispatch/cleanup indefinitely if Mongo is down.
        with mongo_timeout(5):
            collection = self.database_results_collection.with_options(
                write_concern=WriteConcern(w=1, j=True, wtimeout=5000))
            result = collection.update_one({"_id": self.database_results_id}, deepcopy(update), upsert=False)
        if result.acknowledged is not True or result.matched_count != 1:
            raise RuntimeError("Trial evidence write was not acknowledged or its run record is missing.")

    def _record_pending_trial(self, agent, trial, task_context):
        timestamp = self._get_log_timestamp()
        data = {"trial_uuid": trial.trial_uuid, "trial_number": trial.trial_number,
                "agent": agent, "theta": {key: float(value) for key, value in trial.theta.items()},
                "task_context": task_context, "t_0": trial.t_0,
                "prepared_at_utc": timestamp, "updated_at_utc": timestamp,
                "dispatch_state": "prepared"}
        # Keep only this trial's latest in-flight attempt; completed trials use
        # the existing compact nN records, rather than accumulating contexts.
        self._write_results_update({"$set": {self._pending_trial_path(trial): data}})

    def _update_pending_trial(self, trial, **fields):
        fields["updated_at_utc"] = self._get_log_timestamp()
        prefix = self._pending_trial_path(trial) + "."
        self._write_results_update({"$set": {prefix + key: value for key, value in fields.items()}})

    def write_task_result(self, trial: Trial):
        data = {
            "theta": trial.theta,
            "q_metric": trial.task_result.q_metric.to_dict(),
            "t_0": trial.t_0,
            "t_1": trial.t_1,
            "t_delta": trial.t_delta,
            "agent": trial.agent,
            "external": trial.external
        }
        data.update({"trial_uuid": trial.trial_uuid, "task_uuid": trial.task_uuid})
        #logger.debug("Engine::write_task_result.data: " + str(data))
        # One atomic update prevents losing the pending evidence before the
        # ordinary completed result is durable. An ambiguous acknowledgement
        # leaves either the pending evidence or the committed compact result.
        self._write_results_update({"$set": {"n" + str(trial.trial_number): data},
                                    "$unset": {self._pending_trial_path(trial): ""}})
