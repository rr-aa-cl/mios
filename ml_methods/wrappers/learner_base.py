import datetime
import time
from threading import Thread
from queue import Queue
from multiprocessing.pool import ThreadPool
import numpy as np
import uuid
import logging

from abc import ABCMeta, abstractmethod

import requests
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from copy import deepcopy
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from python.utils.ws_client import *


class MetaData:

    def __init__(self):
        self.time_start = None


class LearnerBase(object):
    __metaclass__ = ABCMeta

    def __init__(self):

        self.hosts = None
        self.meta_data = MetaData()

        self.url_lookup = dict()
        self.url_lookup["digital_twin"] = None
        self.url_lookup["knowledge_base"] = None
        self.url_lookup["scheduler"] = None
        self.url_lookup["cros"] = None

        self.n_trial = None
        self.definition = None
        self.preknowledge = None

        self.skill_params_default = None
        self.domain = []
        self.param_template = None
        self.task_params = None
        self.task_template = dict()
        self.mapping = None
        self.base_params = None
        self.map_host_to_alias = dict()

        self.db_self = MongoClient('mongodb://localhost:27017')
        self.db_cos = MongoClient('mongodb://tueirsi-nc-032.local:27017')

        self.options_learner = None
        self.results_task = None
        self.result_id = None
        self.problem = None

        self.flag_stop = False

        self.top_samples = []

        self.data = []

        self.job_queue = Queue()
        self.job_completed = Queue()
        self.flag_stop = False
        self.flag_pause = False
        self.flag_results = True
        self.time_0 = time.time()

        self.hints_uuid = set()
        self.mode = 0

        self.logger = logging.getLogger("ml_service")

    def stop(self):
        self.logger.debug("def_stop")
        self.flag_stop = True
        for address in self.hosts:
            self.logger.debug("Stopping " + address)
            stop_task(address, nominal=True)
        self.logger.debug("def_stop_end")

    def pause(self, pause_state):
        self.logger.debug("Setting pause state to " + str(pause_state))
        self.flag_pause = pause_state

    def init_base(self, hosts=None):
        self.hosts = hosts if hosts else ["localhost"]

        t = Thread(target=self.main_thread)
        t.start()

        self._init_learner()

    def _worker_manager(self, server_list):
        """ thread to manage worker threads """
        managed_threads = []
        current_servers = server_list

        # start worker threads
        for url in server_list:
            print("LoadBalancer: Starting worker thread for %s" % url)
            t = Thread(target=self._worker_thread, args=(url,))
            t.daemon = True
            t.start()
            managed_threads.append({"thread": t, "url": url,
                                    "server_ok": True})

        # monitor worker threads
        while self.flag_stop is False:
            time.sleep(1)
            if len(current_servers) == 0:
                self.flag_stop = True

            if self.flag_stop is True:
                while self.job_queue.qsize() > 0:
                    self.job_queue.get()
                    self.job_queue.task_done()
            bad_servers = False
            for m in managed_threads:
                if not m["thread"].is_alive() and m["url"] in current_servers:
                    print("LoadBalancer: %s not responding, \
                          removing from server list..." % m["url"])
                    current_servers.remove(m["url"])
                    m["server_ok"] = False
                    bad_servers = True

    def set_visualization_url(self, url):
        self.url_lookup["digital_twin"] = url

    def _test_function(self, x):
        return x[0] * x[1]

    def generate_robust_parameters(self, task, instructions):
        task_description = self._get_param_template(task)
        search_filter = dict()
        search_filter["task"] = task
        for p in task_description["id_parameters"]:
            search_filter["task_params." + p] = self.definition[instructions][task]["parameters"][p]
        params = self.db_self.memory.problems.find(search_filter)
        centroid = dict()
        for key, val in task_description["mapping"].items():
            centroid[key] = 0

        n_p = 0
        for p in params:
            n_p += 1
            for key, val in p["parameters"].items():
                centroid[key] += val

        if n_p == 0:
            return None
        for key, val in centroid.items():
            centroid[key] /= n_p

        return centroid

    def map_parameters(self, task, instructions):
        # task_description = self.db_self['mios'].tasks.find_one({"task": task})
        task_description = self._get_param_template(task)
        search_filter = dict()
        search_filter["task"] = task
        for p in task_description["id_parameters"]:
            search_filter["task_params." + p] = self.definition[instructions][task]["parameters"][p]

        db_server = MongoClient('mongodb://' + 'tueirsi-nc-032.local' + ':27017')
        data = db_server.cos.problem_knowledge.find_one(search_filter)
        skills = dict()
        if data is not None:
            t_mapping = task_description['mapping']
            for key, val in data["data"][0].items():
                str_parts = t_mapping[key][0].split(".")
                if str_parts[0] not in skills:
                    skills[str_parts[0]] = dict()
                if str_parts[1] not in skills[str_parts[0]]:
                    skills[str_parts[0]][str_parts[1]] = dict()

                str_parts2 = str_parts[2].split("-")
                skills[str_parts[0]][str_parts[1]][str_parts2[0]] = task_description["skills"][str_parts[0]][str_parts[1]][str_parts2[0]]
                for p in t_mapping[key]:
                    dim = p.split("-")
                    skills[str_parts[0]][str_parts[1]][str_parts2[0]][int(dim[1])-1] = val

            return skills
        return None

    def setup_experiment(self):
        if "setup_instructions" not in self.definition:
            print('Problem definition is missing setup instructions.')
            return False

        if "tasks" not in self.definition["setup_instructions"] or \
                len(self.definition["setup_instructions"]["tasks"]) == 0:
            print("Setup instructions are empty, I will assume that no setup is necessary.")
            return True

        task_list = self.definition["setup_instructions"]["tasks"]
        for t in task_list:
            skills = self.map_parameters(t, "setup_instructions")
            params = self.definition["setup_instructions"][t]
            if skills is not None:
                params["skills"] = skills
            finished = []
            threads = []
            if len(self.hosts) == 0:
                return False
            pool = ThreadPool(processes=len(self.hosts))
            for address in self.hosts:
                threads.append(pool.apply_async(self.setup_experiment_thr, (address, t, params)))

            for thr in threads:
                if thr.get() is True:
                    finished.append(address)

            if not finished:
                return False

        return True

    def setup_experiment_thr(self, address, task, task_parameters):
        while True:
            print("Starting setup for host " + address)
            response = start_task(address, task, task_parameters, True)
            if response is None:
                return False

            if "result" not in response or "task_uuid" not in response["result"]:
                return False

            response = wait_for_task(address, response["result"]["task_uuid"])
            if response is None:
                return False
            print("Finished setup for host " + address)
            if response["result"]["eval"]["error"] != "control_exception":
                break

        if response["result"]["eval"]["success"] is False:
            return False

        return True

    def terminate_experiment(self):
        if "termination_instructions" not in self.definition:
            print('Problem definition is missing termination instructions.')
            return False

        if "tasks" not in self.definition["termination_instructions"] or \
                len(self.definition["termination_instructions"]["tasks"]) == 0:
            print("Termination instructions are empty, I will assume that no termination is necessary.")
            return True

        task_list = self.definition["termination_instructions"]["tasks"]
        for t in task_list:
            skills = self.map_parameters(t, "termination_instructions")
            params = self.definition["termination_instructions"][t]
            if skills is not None:
                params["skills"] = skills

            finished = []
            threads = []
            if len(self.hosts) == 0:
                return False
            pool = ThreadPool(processes=len(self.hosts))
            for address in self.hosts:
                threads.append(pool.apply_async(self.terminate_experiment_thr, (address, t, params)))

            for thr in threads:
                if thr.get() is True:
                    finished.append(address)

            if not finished:
                return False

        return True

    def terminate_experiment_thr(self, address, task, task_parameters):
        while True:
            response = start_task(address, task, task_parameters)
            if response is None:
                return False

            response = wait_for_task(address, response["result"]["task_uuid"])
            if response is None:
                return False
            if response["result"]["eval"]["error"] != "control_exception":
                break

        if response["result"]["eval"]["success"] is False:
            return False

        return True

    def check_syntax_definition(self, definition):

        keywords = ["problem_class", "task", "method_id", "identity_template", "success_criteria", "domain",
                    "reset_instructions", "setup_instructions", "termination_instructions", "parameters", "options"]

        for k in keywords:
            if k not in definition:
                print("Syntax error: Keyword " + k + " is missing in problem definition.")
                return False

        return True

    def load_problem_definition(self, problem_class, identity):
        on_server = False
        on_local = False

        definition = None

        identity[3] = 0
        identity[4] = 0

        definition_server = self.db_cos.cos.problem_definitions.find_one({"problem_class": problem_class,
                                                                         "identity_template": identity})
        if definition_server is None:
            print("Problem definition for class " + problem_class + " does not exist on server.")
        else:
            on_server = True
            del definition_server["_id"]

        definition_local = self.db_self['mios'].ml_problems.find_one({'problem_class': problem_class,
                                                                      "identity_template": identity})
        if definition_local is None:
            print("Problem definition for class " + problem_class + " does not exist locally.")
        else:
            on_local = True
            del definition_local["_id"]

        if on_server is True and on_local is True:
            print('Problem definition has been found on server as well as the local database, overwriting local data.')
            self.db_self['mios'].ml_problems.delete_one({'problem_class': problem_class})
            self.db_self['mios'].ml_problems.insert_one(definition_server)
            definition = definition_server

        if on_server is True and on_local is False:
            print('Problem definition has been found on server but not in local database, uploading data.')
            self.db_self['mios'].ml_problems.insert_one(definition_server)
            definition = definition_server

        if on_server is False and on_local is True:
            print('Problem definition has not been found on server but in local database, uploading data to server.')
            self.db_cos.cos.problem_definitions.insert_one(definition_local)
            definition = definition_local

        if on_server is False and on_local is False:
            print('Problem definition has not been found on server or in local database, aborting.')
            return None

        if self.check_syntax_definition(definition) is False:
            print("Syntax check for problem definition failed.")
            return None

        return definition

    def learn_task(self, problem_class, identity_instance, preknowledge=None, setup=True, terminate=True,
                   mode=0, tags=[], write_results=True):
        if len(self.hosts) == 0:
            print("No robot url provided, aborting.")
            return False

        print("Started learning of problem class " + problem_class + " with identity " + str(identity_instance))
        self.mode = mode
        if self.mode == 1:
            print("This is a test run, I will wait 3 second before returning.")
            time.sleep(3)
            while self.flag_pause is True:
                print("Service has been paused.")
                time.sleep(1)
            return True

        self.db_self = MongoClient('mongodb://localhost:27017')
        self.flag_results = write_results

        self.definition = self.load_problem_definition(problem_class, identity_instance.copy())
        if self.definition is None:
            print("Error while loading problem definition.")
            return False

        identity = identity_instance

        if identity[3] + identity[4] > 1:
            print("Invalid cost function weights.")
            return False

        self.problem = {
            "problem_class": problem_class,
            "identity": identity
        }
        date = datetime.datetime.now()
        date_str = str(date.year) + str(date.month) + str(date.day) + \
                   '_' + str(date.hour) + str(date.minute)

        print("Checking domains.")
        # for url in self.rpc_url:
        #     if self._check_domain(url) is False:
        #         print('Encountered error while checking domain on url ' + url + '.')
        #         return False
        #     if self._check_mapping(url) is False:
        #         print('Encountered error while checking mapping on url ' + url + '.')
        #         return False

        base_identity = None
        self.preknowledge = preknowledge
        if self.preknowledge is not None:
            if "base_identity" not in self.preknowledge:
                print("Preknowledge is missing the base problem identity. I will assume none.")
                self.preknowledge["base_identity"] = None
            else:
                base_identity = self.preknowledge["base_identity"]
            if "source" not in self.preknowledge:
                print("Source of preknowledge has not been defined, I will assume local.")
                self.preknowledge["source"] = "local"

        experiment = {"meta": {
            "identity": identity,
            "date": date_str,
            "uuid": str(uuid.uuid4()),
            "base_identity": None,
            "tags": tags,
            "nominal": False
        }}

        task_description = self.db_self['mios'].tasks.find_one({"name": self.definition["task"]})
        self.definition['mapping'] = task_description['mapping']

        if self._read_config(self.db_self) is False:
            print('Error configuring learning problem.')
            return False

        if self.preknowledge is not None and False is True:
            if self.preknowledge["base_identity"] == "any":
                if self.preknowledge["source"] == "local":
                    print("Looking for similar problems locally...")
                    self.base_params, id_similar = self.find_most_similar_problem_local(self.problem["identity"])
                    experiment["meta"]["base_identity"] = id_similar
                if self.preknowledge["source"] == "global":
                    if self.url_lookup["knowledge_base"] is not None:
                        print("Looking for similar problem globally...")
                        response = self.rpc_call(self.url_lookup["knowledge_base"], 'get_similar_knowledge',
                                            {'identity': self.problem["identity"]})
                        if response is None:
                            print('Response from knowledge server is None.')
                        elif "result" not in response:
                            print('Response from knowledge server has no result.')
                        elif response['result']['result'] is False:
                            print('Knowledge server did not return requested knowledge.')
                        elif response['result']['result'] is True:
                            self.base_params = response['result']['knowledge']
                            experiment["meta"]["base_identity"] = response["result"]["identity"]
            elif self.preknowledge["base_identity"] is not None:
                identity = self.preknowledge["base_identity"]
                if self.download_pre_knowledge(identity, preknowledge["base_problem"]) is False:
                    print("Could not download requested knowledge, aborting learning process.")
                    return False

        if setup is True:
            print("Starting experiment setup.")
            if self.setup_experiment() is False:
                return False
                print('Experiment setup has failed. I will lock the robot and pause the '
                      'learning service until confirmation.')
                #self.rpc_call(self.rpc_url[0], 'lockdown_core', None)
                self.pause(True)
                if self.url_lookup["scheduler"] is not None:
                    self.rpc_call(self.url_lookup["scheduler"], 'pause_experiment', None)

        if self.flag_pause is True:
            print("You can continue the learning process by calling the method 'unpause_learning' with the parameter"
                  " 'lift_lockdown: True'.")
        #rpc_call("http://" + self.hosts[0] + ":8383", "set_led", {"pattern": "attention"})
        while self.flag_pause is True:
            time.sleep(1)

        if self.flag_results is True:
            self.results_task = self.db_self.ml_results[self.problem["problem_class"]]
            self.result_id = self.results_task.insert_one(experiment).inserted_id

        if self.flag_stop is True:
            return False

        self.n_trial = 1
        self.meta_data.time_start = time.time()
        self._learn_task()

        print("Uploading knowledge")
        self.upload_local_knowledge()
        if self.flag_results is True:
            self.results_task.update_one({'_id': self.result_id}, {'$set': {"meta.nominal": True}}, upsert=False)
        if self.preknowledge is not None and self.preknowledge["source"] == "global":
            self.upload_global_knowledge()
        if terminate is True:
            if self.terminate_experiment() is False:
                print('Experiment termination has failed. I will lock the robot and pause the learning '
                      'service until confirmation.')
                print(self.hosts)
                #self.rpc_call(self.rpc_url[0], 'lockdown_core', None)
                self.pause(True)
                if self.url_lookup["scheduler"] is not None:
                    self.rpc_call(self.url_lookup["scheduler"], 'pause_experiment', None)
                return True

        print("You can continue the learning process by calling the method 'unpause_learning' with the parameter"
              " 'lift_lockdown: True'.")
        self.pause(False)
        #self.rpc_call(self.rpc_url[0], "set_led", {"pattern": "attention"})
        while self.flag_pause is True:
            time.sleep(1)

        return True

    def download_pre_knowledge(self, identity, similar_problem=None):
        if self.url_lookup["knowledge_base"] is None:
            print("Knowledge base is not available.")
            return False
        try:
            if similar_problem is None:
                response = self.rpc_call(self.url_lookup["knowledge_base"], 'get_similar_knowledge',
                                    {'problem_id': identity["problem_id"], 'n_samples': 1})
                if response is None:
                    print('Response from knowledge server is None.')
                    return False
                if response['result']['result'] is False:
                    print('Knowledge server did not return requested knowledge.')
                    return False
                if response['result']['result'] is True:
                    self.base_params = response['result']['problem_knowledge'][0]
                    return True
            else:
                response = self.rpc_call(self.url_lookup["knowledge_base"], 'download_knowledge',
                                    {'identity': identity, 'n_samples': 1})
                if response is None:
                    print('Response from knowledge server is None.')
                    return False
                if response['result']['result'] is False:
                    print('Knowledge server did not return requested knowledge.')
                    return False
                if response['result']['result'] is True:
                    self.base_params = response['result']['problem_knowledge'][0]
                    return True
        except KeyError as e:
            print('Response from knowledge server was faulty: ' + str(e))
            return False

    def upload_local_knowledge(self):
        doc = self.results_task.find_one({"_id": ObjectId(self.result_id)})
        del doc["_id"]
        self.db_self.ml_results_tmp[self.problem["problem_class"]].insert_one(doc)
        self.process_knowledge()

    def upload_global_knowledge(self):
        if self.url_lookup["knowledge_base"] is None:
            return False

        doc = self.results_task.find_one({"_id": ObjectId(self.result_id)})
        del doc["_id"]
        self.db_cos.ml_results_tmp[self.problem["problem_class"]].insert_one(doc)
        self.rpc_call(self.url_lookup["knowledge_base"], "update_knowledge")
        return True

    def _check_domain(self, url):

        url = url.split(':')[1].split('/')
        client = MongoClient('mongodb://' + url[2] + ':27017')
        db_mios = client['mios']
        task_description = db_mios.tasks.find_one({"name": self.definition["task"]})

        if task_description is None:
            print('Could not find task with id ' + self.definition["task"] + ' in local knowledge base.')
            return False

        if 'domain' not in self.definition:
            print('Problem definition does not have a domain struct.')
            return False

        if 'mapping' not in task_description:
            print('Mapping is not in description of task.')
            return False

        for key, val in self.definition['domain'].items():
            if key not in task_description['mapping']:
                print("Parameter " + key + " is not in parameter mapping.")
                return False

        for key, val in task_description['mapping'].items():
            if key not in self.definition['domain']:
                print("Parameter " + key + " is not in domain.")
                return False

        return True

    def _check_mapping(self, url):
        url = url.split(':')[1].split('/')
        client = MongoClient('mongodb://' + url[2] + ':27017')
        db_mios = client['mios']
        task_description = db_mios.tasks.find_one({"name": self.definition["task"]})
        if task_description is None:
            print('Task description for task ' + self.definition["task"] + ' does not exist.')
            return False

        for key, val in task_description['mapping'].items():
            for p in val:
                skill = p.split('.')
                if 'skills' not in task_description:
                    print('Task description has no field "skills".')
                    return False
                if skill[0] not in task_description["skills"]:
                    print('Task description does not contain a skill with name ' + skill[0] + '.')
                    return False
                if 'type' not in task_description["skills"][skill[0]]:
                    print('Skill ' + skill[0] + ' in task description of task ' + self.definition["task"] +
                          ' does not have a type.')
                    return False
                skill_type = task_description["skills"][skill[0]]["type"]
                parameter_category = skill[1]
                parameter = skill[2].split('-')
                parameter_name = parameter[0]
                parameter_dim = int(parameter[1])
                if parameter_category == 'skill':
                    skill_description = db_mios.skills.find_one({"name": skill_type})
                    if skill_description is None:
                        print('Skill of type ' + skill_type + ' does not exist.')
                        return False
                    if parameter_name not in skill_description:
                        print('Parameter ', parameter_name, ' not in skill of type ', skill_type, '.')
                        return False
                    if parameter_dim > len(skill_description[parameter_name]):
                        print('Parameter ', parameter_name, ' has less than ', parameter_dim, ' dimensions.')
                        return False
                if parameter_category == 'control':
                    params_control = db_mios.parameters.find_one({'type': 'control'})
                    if parameter_name not in params_control:
                        print('Parameter ', parameter_name, ' is not a controller parameter.')
                        return False
                    if parameter_dim > len(params_control[parameter_name]):
                        print('Parameter ', parameter_name, ' has less than ', parameter_dim, ' dimensions.')
                        return False

        return True

    def _add_param(self, dic, keys, defaults, dim, value):
        # create parameter and add to dic given an array of keys
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
            defaults = defaults[key]
        # set parameter to default
        dic[keys[-1]] = defaults[keys[-1]]
        # set parameter at dim to value
        dic[keys[-1]][dim - 1] = value

    def _set_param(self, x, i, params):
        p = self.mapping[self.domain[i]["name"]]
        params["domain"][self.domain[i]["name"]] = float(x)
        for k in p:
            cat = k.split(".")
            cat2 = cat[2].split("-")
            params['skills'][cat[0]][cat[1]][cat2[0]][int(cat2[1]) - 1] = float(np.asscalar(x))
        # params['skills'][self.domain[i]['skill']][self.domain[i]['category']][self.domain[i]['name_orig']][self.domain[i]['dim']-1]=np.asscalar(x)

    def _write_meta_data(self, n_trial, params, cost, success, t_start, t_finish, constraints=None):
        meta_data = dict()
        meta_data['parameters'] = params
        meta_data['cost'] = cost
        meta_data['success'] = success
        meta_data["t_start"] = t_start
        meta_data['t_duration'] = t_finish - t_start
        meta_data["t_finish"] = t_finish
        if constraints is not None:
            meta_data['constraints'] = constraints

        if self.flag_results is True:
            self.results_task.update_one({'_id': self.result_id}, {'$set': {'n' + str(n_trial): meta_data}}, upsert=False)

    def _get_param_template(self, task):
        param_template = self.db_self.mios.tasks.find_one({"name": task})
        param_template["domain"] = dict()
        param_template["task"] = task

        skills = dict()
        skill_types = dict()
        for key, val in param_template["skills"].items():
            if 'type' not in val:
                print('Skill ' + key + ' has no type definition.')
                return False

            skills[key] = val['type']
            if val['type'] not in skill_types:
                skill_types[val['type']] = self.db_self.mios.skills.find_one({"name": val["type"]})

        params_control = self.db_self.mios.parameters.find_one({"type": "control"})
        params_user = self.db_self.mios.parameters.find_one({"type": "user"})

        for key, val in param_template["mapping"].items():
            for p in val:
                cat = p.split(".")
                cat2 = cat[2].split("-")
                if cat[0] not in param_template["skills"]:
                    param_template["skills"][cat[0]] = dict()
                if cat[1] not in param_template["skills"][cat[0]]:
                    param_template["skills"][cat[0]][cat[1]] = dict()
                if cat[1] == "control":
                    if cat2[0] not in param_template["skills"][cat[0]][cat[1]]:
                        param_template["skills"][cat[0]][cat[1]][cat2[0]] = params_control[cat2[0]]
                if cat[1] == "user":
                    if cat2[0] not in param_template["skills"][cat[0]][cat[1]]:
                        param_template["skills"][cat[0]][cat[1]][cat2[0]] = params_user[cat2[0]]
                if cat[1] == "skill":
                    if cat2[0] not in param_template["skills"][cat[0]][cat[1]]:
                        param_template["skills"][cat[0]][cat[1]][cat2[0]] = skill_types[skills[cat[0]]][cat2[0]]

        del param_template['_id']
        return param_template

    def _read_config(self, db_client):

        db_mios = db_client['mios']

        self.param_template = db_mios.tasks.find_one({"name": self.definition["task"]})
        self.param_template["domain"] = dict()
        self.param_template["task"] = self.definition["task"]
        self.param_template["queue_task"] = True
        self.param_template["identity"] = self.problem["identity"]
        self.param_template["w_cost_function"] = self.problem["identity"][3:]

        if 'parameters' in self.definition:
            for key,val in self.definition["parameters"].items():
                if key not in self.param_template["parameters"]:
                    print('Parameter ' + key + ' does not exist in task description of task ' + self.param_template["task"] + '.')
                else:
                    self.param_template["parameters"][key] = self.definition["parameters"][key]

        del self.param_template['_id']

        domain = self.definition["domain"]
        self.mapping = self.definition["mapping"]

        skills = dict()
        skill_types = dict()
        for key,val in self.param_template["skills"].items():
            if 'type' not in val:
                print('Skill ' + key + ' has no type definition.')
                return False

            skills[key] = val['type']

            if val['type'] not in skill_types:
                skill_type = db_mios["skills"].find_one({"name": val["type"]})
                if skill_type is None:
                    print("I did not find any skill of type " + val['type'] + ".")
                    return False
                else:
                    skill_types[val['type']] = skill_type

        params_control = db_mios["parameters"].find_one({"type": "control"})
        params_user = db_mios["parameters"].find_one({"type": "user"})

        for key, val in self.mapping.items():
            for p in val:
                cat = p.split(".")
                cat2 = cat[2].split("-")
                if cat[0] not in self.param_template["skills"]:
                    self.param_template["skills"][cat[0]] = dict()
                if cat[1] not in self.param_template["skills"][cat[0]]:
                    self.param_template["skills"][cat[0]][cat[1]] = dict()
                if cat[1] == "control":
                    if cat2[0] not in self.param_template["skills"][cat[0]][cat[1]]:
                        self.param_template["skills"][cat[0]][cat[1]][cat2[0]] = params_control[cat2[0]]
                if cat[1] == "user":
                    if cat2[0] not in self.param_template["skills"][cat[0]][cat[1]]:
                        self.param_template["skills"][cat[0]][cat[1]][cat2[0]] = params_user[cat2[0]]
                if cat[1] == "skill":
                    if cat2[0] not in self.param_template["skills"][cat[0]][cat[1]]:
                        self.param_template["skills"][cat[0]][cat[1]][cat2[0]] = skill_types[skills[cat[0]]][cat2[0]]

        for key, val in domain.items():
            param = dict()
            param['name'] = key
            param['bounds'] = (val['min'], val['max'])
            self.domain.append(param)

        if 'method_id' not in self.definition:
            print('Problem definition does not contain a method_id.')
            return False

        options = self.db_self['mios']["ml_methods"].find_one({"method": self.definition["method_id"]})
        if options is None:
            print('Local knowledge base has no options for ' + self.definition["method_id"] + '.')
            return False

        if self._read_local_options(options) is False:
            print('Error when reading method options.')
            return False

        return True

    @staticmethod
    def read_option(o, d):
        if o in d:
            return d[o]
        else:
            return None

    @abstractmethod
    def _init_learner(self):
        pass

    @abstractmethod
    def _learn_task(self):
        pass

    @abstractmethod
    def _read_local_options(self, default_options):
        pass

    @abstractmethod
    def _setup_exp(self):
        pass

    @abstractmethod
    def _run_trial(self, x):
        pass

    @abstractmethod
    def _terminate_exp(self):
        pass

    @abstractmethod
    def _transform_to_real(self,x):
        pass

    def _get_param_index(self, p):
        for i in range(len(self.bounds)):
            if self.bounds[i]['name'] == p:
                return i

    def comp_dict(self, d1, d2):
        for key, val in d1.items():
            if key not in d2:
                return False
            elif not isinstance(val, dict):
                pass
            else:
                return self.comp_dict(val, d2[key])
        for key, val in d2.items():
            if key not in d1:
                return False
            elif not isinstance(val, dict):
                pass
            else:
                return self.comp_dict(val, d1[key])
        return True

    def process_problem_knowledge(self, problem_class, identity, threshold=0.1):
        data_selection = []
        cnt = 0
        for doc in self.db_self.ml_results_tmp[problem_class].find(
                {"meta.identity": identity}):
            data = []
            for key, val in doc.items():
                if key != "meta" and key != "_id":
                    if val["success"] is True and val["cost"] != 0:
                        data.append(val)
            data_sorted = sorted(data, key=lambda i: i["cost"])
            for i in range(int(threshold * len(data_sorted))):
                parameters = []
                for key_p, val_p in data_sorted[i]["parameters"]["domain"].items():
                    parameters.append(val_p)

                data_selection.append(parameters)
                cnt += 1

        if len(data_selection) == 0:
            return None
        x = np.asarray(data_selection)
        x_norm = StandardScaler().fit_transform(x)
        clustering = DBSCAN(eps=10, min_samples=10).fit(x_norm)

        labels_map = clustering.labels_
        cluster = [[]]
        labels = []
        # for l in labels_map:
        #     if l != -1:
        #         if l not in labels:
        #             labels.append(l)
        #             cluster.append([])

        for i in range(len(x)):
            cluster[0].append(x[i])
            if labels_map[i] != -1:
                pass

        centroids = []
        for c in cluster:
            centroids.append(self.get_centroid(np.asarray(c)))

        return centroids

    def process_knowledge(self):
        pass
        # doc = self.db_cos.cos.problem_definitions.find_one({"problem_class": self.problem["problem_class"]})
        # if doc is None:
        #     print("Problem class " + self.problem["problem_class"] + " has no definition.")
        #     return False
        # if doc["problem_class"] not in self.db_self.ml_results_tmp.list_collection_names():
        #     return False
        # centroids = self.process_problem_knowledge(self.problem["problem_class"], self.problem["identity"])
        # if centroids is None:
        #     return False
        # data = []
        # for c in centroids:
        #     cnt_p = 0
        #     data.append(dict())
        #     for key, val in doc["domain"].items():
        #         data[-1][key] = c[cnt_p]
        #         cnt_p += 1
        #
        # knowledge = {
        #     "identity": self.problem["identity"],
        #     "data": data,
        #     "task": doc["task"],
        #     "task_params": doc["parameters"]
        # }
        # filter = {
        #     "identity": self.problem["identity"]
        # }
        # if self.db_self.mios.problem_knowledge.find_one(filter) is not None:
        #     self.db_self.mios.problem_knowledge.delete_one(filter)
        # self.db_self.mios.problem_knowledge.insert(knowledge)

    def get_centroid(self, arr):
        length, dim = arr.shape
        return np.array([np.sum(arr[:, i]) / length for i in range(dim)])

    def get_problem_distance(self, id1, id2):
        dist_geometry = np.sqrt(np.power(id1[0]-id2[0], 2)+np.power(id1[1]-id2[1], 2)+np.power(id1[2]-id2[2], 2))
        dist_cost = np.sqrt(np.power(id1[3]-id2[3], 2)+np.power(id1[4]-id2[4], 2))
        dist_total = dist_geometry + dist_cost * 10
        dist_total_norm = 1 - np.exp(-dist_total)
        print("DISTANCE: " + str(dist_total))
        print("DISTANCE_n: " + str(dist_total_norm))
        return dist_total_norm

    def find_most_similar_problem_local(self, identity):
        min_dist = 1
        min_doc = None
        for doc in self.db_self.mios.problem_knowledge.find({}):
            if "identity" not in doc:
                continue
            dist = self.get_problem_distance(identity, doc["identity"])
            if dist < min_dist:
                min_dist = dist
                min_doc = doc

        if min_doc is not None:
            return min_doc["data"][0], min_doc["identity"]
        else:
            return None, None

    def check_for_success(self):
        success = [d["success"] for d in self.data]
        cost = [d["cost"] for d in self.data]
        ma_success = self.moving_average(success, 10)
        thr_cost = False
        thr_success = False
        success_criteria = self.definition["success_criteria"]
        xp = np.linspace(0, 1, len(success_criteria["cost"]))
        fp = success_criteria["cost"]
        cost_thr = np.interp(self.problem["identity"][4], xp, fp)
        for i in range(len(cost)):
            if cost[i] < cost_thr and cost[i] > 0:
                thr_cost = True
                break
        for i in range(len(ma_success)):
            if ma_success[i] > success_criteria["success"]:
                thr_success = True
                break

        return thr_cost and thr_success

    def moving_average(self, arr, window):
        weights = np.repeat(1, window) / window
        sma = np.convolve(arr, weights, "valid")
        return sma

    def lift_lockdown(self):
        call_method(self.hosts[0], 'lift_core_lockdown', None)

    def main_thread(self):
        unresponsive_hosts = set()
        worker_threads = dict()
        for h in self.hosts:
            worker_threads[h] = None
        cnt_jobs = 0
        while self.flag_stop is False:
            print("##################################")
            print("LEN BEFORE: " + str(self.job_queue.qsize()))
            job = self.job_queue.get()
            print("LEN AFTER: " + str(self.job_queue.qsize()))
            print("##################################")
            thread_started = False

            while self.flag_stop is False and thread_started is False:
                for h in self.hosts:
                    if worker_threads[h] is not None and worker_threads[h].is_alive() is True:
                        continue

                    response = call_method(h, "is_busy", silent=True)
                    if response is None:
                        continue

                    worker_threads[h] = Thread(target=self._worker_thread, args=(h, job, ))
                    worker_threads[h].start()
                    cnt_jobs += 1
                    print("Threads started: " + str(cnt_jobs))
                    thread_started = True
                    break

                time.sleep(0.1)
        print("FINISHED")
        for h in self.hosts:
            if worker_threads[h] is not None:
                worker_threads[h].join(1000)
        print("EMPTY QUEUE")
        while self.job_queue.empty() is False:
            try:
                self.job_queue.task_done()
            except ValueError as e:
                pass
        print("DONE")

    def _worker_thread(self, address, job):
        cnt_repeat = 0
        max_repeat = 3
        msg_pause = False
        job_done = False

        if "reset_instructions" not in job:
            print("Problem definition does not contain reset instructions, aborting...")
            return

        print("START")
        while cnt_repeat < max_repeat and self.flag_stop is False:
            if self.flag_pause is True:
                if msg_pause is False:
                    print("Service is paused.")
                    msg_pause = True
                time.sleep(1)
                continue
            else:
                msg_pause = False

            # start task
            job["t_start"] = time.time()
            task = job["params"]["task"]
            task_parameters = job["params"]
            print("EXECUTE")
            network_ok, process_ok, evaluation = self.execute_task(address, task, task_parameters)
            print("AFTER EXECUTE")
            if network_ok is False:
                cnt_repeat += 1
                print("Network was not ok at execute_task.")
                time.sleep(1)
                continue
            if process_ok is False:
                print("Process was not ok at execute_task.")
                break
            if evaluation is None:
                print("Result was none at execute_task.")
                break
            if evaluation["error"] == "control_exception":
                print("Control exception occured.")
                cnt_repeat += 1
                continue

            job["response"] = evaluation
            job["t_finish"] = time.time()
            success = evaluation["success"]
            print("#########################################")
            print("JOB_ID: " + str(job["id"]) + ", ADDRESS: " + address)
            print(evaluation)
            print("#########################################")
            if success is True:
                cost = evaluation['cost_suc']
            else:
                cost = evaluation['cost_err']

            data_sample = dict()
            data_sample["success"] = success
            data_sample["cost"] = cost
            self.data.append(data_sample)
            job_done = True

            self.push_to_knowledge_server(address, job["params_normalized"], cost, success)
            break

        # reset task
        cnt_repeat = 0
        print("RESET")
        while cnt_repeat < max_repeat:
            if self.flag_pause is True:
                if msg_pause is False:
                    print("Service is paused.")
                    msg_pause = True
                time.sleep(1)
                continue
            else:
                msg_pause = False

            network_ok, process_ok, evaluation = self.reset_procedure(address, job["reset_instructions"])
            if network_ok is False:
                cnt_repeat += 1
                print("Network was not ok as reset_procedure.")
                time.sleep(1)
                continue
            if process_ok is False:
                print("Process was not ok at reset_procedure.")
                break
            if evaluation is not None:
                if evaluation["error"] == "control_exception":
                    print("Control exception occured.")
                    cnt_repeat += 1
                    continue

            break

        stop_task(address, nominal=True, recover=True, empty_queue=True)
        self.job_queue.task_done()
        if job_done is False:
            print("Job has not been finished properly. It is re-inserted into the job queue.")
            self.job_queue.put(deepcopy(job))
        else:
            print("Job has been finished.")
            self.job_completed.put(job)
        return

    # Returns: Network ok, process ok, result
    def reset_procedure(self, address, reset_instructions):

        task_list = reset_instructions["tasks"]
        evaluation = None
        print("Resetting robot with hostname " + address + ".")

        for t in task_list:
            if t not in reset_instructions:
                print('Task ' + t + ' was declared in the reset instructions but not defined.')
                return True, False, None

            params = reset_instructions[t]

            task = t
            task_parameters = params
            network_ok, process_ok, evaluation = self.execute_task(address, task, task_parameters)
            if network_ok is False:
                return False, False, None
            if process_ok is False or eval is None:
                return True, False, None

        return True, True, evaluation

    # Returns: connection is ok, process was ok, result
    def execute_task(self, address, task, parameters):
        print("Executing task " + task + " for robot with hostname " + address + ".")
        response = start_task(address, task, parameters, True)
        if response is None:
            print("Response from calling start_task on host " + address + " was none.")
            return False, False, None
        if "result" not in response:
            print("Response from calling start_task on host " + address + " did not contain any result.")
            print("############################")
            print(response)
            print("############################")
            return True, False, None
        if "task_uuid" not in response["result"]:
            print("Response from calling start_task on host " + address + " did not contain a task uuid.")
            print("############################")
            print(response)
            print("############################")
            return True, False, None

        response = wait_for_task(address, response["result"]["task_uuid"], )
        print("Task " + task + " for robot with hostname " + address + " has finished.")
        if response is None:
            print("Response from calling wait_for_task on host " + address + " did not contain any result.")
            return False, False, None
        if "result" not in response:
            print("Response from calling wait_for_task on host " + address + "did not contain any result.")
            print("############################")
            print(response)
            print("############################")
            return True, False, None
        if "eval" not in response["result"]:
            print("Response from calling wait_for_task on host " + address + "did not contain any eval.")
            print("############################")
            print(response)
            print("############################")
            return True, False, None
        evaluation = response["result"]["eval"]
        return True, True, evaluation

    def push_to_knowledge_server(self, address, parameters_normalized, cost, success):
        data_elem = {
            "parameters": parameters_normalized,
            "cost": cost,
            "success": success
        }
        hint_uuid = str(uuid.uuid4())
        params_hints = {
            "data": data_elem,
            "identity": self.problem["identity"],
            "uuid": hint_uuid
        }

        self.hints_uuid.add(hint_uuid)
        if self.url_lookup["knowledge_base"] is None:
            return
        else:
            if self.preknowledge is not None and self.preknowledge["source"] == "global":
                response = self.rpc_call(self.url_lookup["knowledge_base"], "push_hints", params_hints)
                if response is None:
                    print("Knowledge base is not reachable at address " + str(self.url_lookup["knowledge_base"]) +
                          " from host " + address + ".")

        if self.url_lookup["digital_twin"] is not None and self.map_host_to_alias is not None:
            response = self.rpc_call(self.url_lookup["digital_twin"], 'update_visualization', {
                'params': {'cost': cost, 'parameters': parameters_normalized, 'hostname': address,
                           "alias": self.map_host_to_alias[address], 'success': success}}, timeout=1)
            if response is None:
                print("Digital Twin is not reachable at address " + str(self.url_lookup["digital_twin"]) +
                      " from host " + address + ".")

    def rpc_call(self, url, method, params=None, timeout=2000):
        headers = {'content-type': 'application/json'}
        if params is None:
            params = {None: None}

        payload = {
            u"method": method,
            u"params": params if params else u"",
            u"jsonrpc": u"2.0",
            u"id": 0,
        }
        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=timeout).json()
        except requests.Timeout as e:
            print('Timeout, server has terminated or does not exist: ' + str(e))
            response = None
        except requests.ConnectionError as e:
            print('Connection error, target url not reachable:' + str(e))
            response = None
        except TypeError as e:
            print("JSON Error: " + str(e))
            response = None

        return response
