#!/usr/bin/python3 -u
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from jsonrpc import JSONRPCResponseManager, dispatcher

from threading import Thread
import uuid
from pymongo import MongoClient
from copy import deepcopy
import requests
import json
import socket
import time

from ml_methods.wrappers.learner_cmaes import LearnerCMAES
from ml_methods.wrappers.learner_lhs import LearnerLHS
from ml_methods.wrappers.learner_forest import LearnerForest


def rpc_call(url, method, params=None):
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
        response = requests.post(url, data=json.dumps(payload), headers=headers).json()
    except requests.Timeout:
        print('Timeout, server has terminated or does not exist.')
        response = None
    except requests.ConnectionError:
        print('Connection error, target url not reachable.')
        response = None

    return response


class Scheduler:
    def __init__(self):
        self.learner = None

        self.active_problems = []
        self.closed_problems = []
        self.failed_problems = []

        self.active_robots = []

        self.url_lookup = dict()
        self.url_lookup["digital_twin"] = None
        self.url_lookup["knowledge_base"] = None
        self.url_lookup["scheduler"] = None
        self.url_lookup["cros"] = None

        t = Thread(target=self.listen_for_servers)
        t.start()

    def listen_for_servers(self):
        sockets = []
        ports = [50001, 50002, 50003, 50004]
        for p in ports:
            sockets.append(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
            sockets[-1].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sockets[-1].bind(("<broadcast>", p))
            sockets[-1].settimeout(0.1)
        while True:

            for s in sockets:
                try:
                    m = s.recvfrom(1024)
                    data = json.loads(m[0])
                    if "designation" in data and data["designation"] in self.url_lookup:
                        self.url_lookup[data["designation"]] = "http://" + data["ip"] + ":" + str(data["port"])
                except (socket.timeout, json.decoder.JSONDecodeError):
                    pass

                if self.learner is not None:
                    self.learner.url_lookup = self.url_lookup

            time.sleep(1)

    def learn_task(self, urls, problem_class, method_id, identity_instance, preknowledge,
                   sub_uuid, setup, terminate, mode, hosts, tags, write_results):
        print(method_id)
        if method_id == 'cmaes':
            self.learner = LearnerCMAES()
        elif method_id == 'lhs':
            self.learner = LearnerLHS()
        elif method_id == 'forest':
            self.learner = LearnerForest()
        else:
            print("Method " + method_id + " is unknown.")
            return False

        print('Starting to learn problem ' + problem_class + ' with method ' + method_id + '.')
        self.learner.init_base(urls)
        self.learner.url_lookup = self.url_lookup
        self.active_robots = urls
        # success = False
        # success = self.learner.learn_task(problem_id, name, overwrite, use_preknowledge)
        # return success
        # try:
        self.learner.map_host_to_alias = hosts
        self.active_problems.append(sub_uuid)
        success = self.learner.learn_task(problem_class, identity_instance, preknowledge, setup,
                                          terminate, mode, tags, write_results)
        # except (TypeError, IndexError, KeyError) as e:
        #     print('Caught exception')
        #     print(e)
        #     success = False

        self.active_problems.remove(sub_uuid)
        if success is True:
            self.closed_problems.append(sub_uuid)
        else:
            print('Append to failed problems.')
            self.failed_problems.append(sub_uuid)
            if self.url_lookup["scheduler"] is not None:
                self.learner.rpc_call(self.url_lookup["scheduler"], "stop_scheduler", None)

        self.learner = None
        print('Finished learning')
        return success

    def stop_learning(self):
        print("STOP")
        if self.learner is None:
            return
        else:
            self.learner.stop()

    def pause_learning(self, pause_state, lift_lockdown=False):
        if self.learner is not None:
            if lift_lockdown is True:
                self.learner.lift_lockdown()
            self.learner.pause(pause_state)

    def is_busy(self):
        if self.learner is None:
            return False
        else:
            return True

    def set_visualization_url(self, url):
        self.url_lookup["digital_twin"] = "http://" + url + ":4000"


class LearningServer:

    def init(self):
        global S
        S = Scheduler()
        run_simple('0.0.0.0', 9002, self.start_server)

    @Request.application
    def start_server(self, request):
        response = JSONRPCResponseManager.handle(request.data, dispatcher)
        return Response(response.json, mimetype='application/json')

    @dispatcher.add_method
    def upload_knowledge(**kwargs):
        if "problem_id" not in kwargs:
            print("Missing parameter: problem_id")
            return

        problem_id = kwargs["problem_id"]

        db_self = MongoClient("mongodb://localhost:27017")
        for doc in db_self.ml_results[problem_id].find({}):
            i_best = 0
            cnt_best = 1
            min_cost = doc["n1"]["cost"]
            for key, val in doc.items():
                if key != "name" and key != "_id" and key != "date":
                    if val["cost"] < min_cost and val["cost"] != 0:
                        min_cost = val["cost"]
                        i_best = cnt_best
                    cnt_best += 1

            problem_data = dict()
            problem_data["problem_id"] = problem_id
            problem_data["task_id"] = doc["n" + str(i_best)]["parameters"]["task_id"]
            problem_data["task_params"] = doc["n" + str(i_best)]["parameters"]["parameters"]
            problem_data["parameters"] = deepcopy(doc["n" + str(i_best)]["parameters"]["domain"])
            problem_data["cost"] = doc["n" + str(i_best)]["cost"]
            problem_data["success"] = doc["n" + str(i_best)]["success"]
            response = rpc_call("http://tueirsi-nc-032.local:8500", 'upload_knowledge', {'problem_data': problem_data})

    @dispatcher.add_method
    def learn_task(**kwargs):
        preknowledge = None
        setup = True
        terminate = True
        mode = 0
        hosts = None
        tags = []
        write_results = True
        if "problem_class" not in kwargs:
            print("Missing parameter: problem_class")
            return
        if "method_id" not in kwargs:
            print("Missing parameter: method_id")
            return
        if "identity_instance" not in kwargs:
            print("Missing parameter: identity_instance")
            return
        if "urls" not in kwargs:
            print("No robot URLs have been specified, I will only use localhost.")
            kwargs["urls"] = "localhost"
        if "preknowledge" in kwargs:
            preknowledge = kwargs["preknowledge"]
        if "setup" in kwargs:
            setup = kwargs["setup"]
        if "terminate" in kwargs:
            terminate = kwargs["terminate"]
        if "mode" in kwargs:
            mode = kwargs["mode"]
        if "hosts" in kwargs:
            hosts = kwargs["hosts"]
        if "tags" in kwargs:
            tags = kwargs["tags"]
        if "write_results" in kwargs:
            tags = kwargs["write_results"]
        global S

        if S.is_busy():
            print('Learner is busy')
            return

        sub_uuid = str(uuid.uuid4())
        t = Thread(target=S.learn_task, args=(kwargs["urls"], kwargs["problem_class"], kwargs["method_id"],
                                              kwargs["identity_instance"], preknowledge, sub_uuid, setup, terminate,
                                              mode, hosts, tags, write_results))
        t.start()
        response = {
            "problem_uuid": sub_uuid
        }
        return response

    @dispatcher.add_method
    def stop_learn(**kwargs):
        global S
        t = Thread(target=S.stop_learning)
        t.start()

    @dispatcher.add_method
    def pause_learning(**kwargs):
        global S
        S.pause_learning(True)

    @dispatcher.add_method
    def unpause_learning(**kwargs):
        lift_lockdown = False
        if "lift_lockdown" in kwargs:
            lift_lockdown = kwargs["lift_lockdown"]
        global S
        S.pause_learning(False, lift_lockdown)

    @dispatcher.add_method
    def is_busy(**kwargs):
        global S
        response = {
            "busy": S.is_busy()
        }
        return response

    @dispatcher.add_method
    def get_problem_status(**kwargs):
        print('STATUS')
        print(kwargs)
        global S
        if "problem_uuid" not in kwargs:
            print("Missing parameter: problem_uuid")

        response = dict()
        if kwargs["problem_uuid"] in S.active_problems:
            response["status"] = "active"
        elif kwargs["problem_uuid"] in S.closed_problems:
            response["status"] = "closed"
        elif kwargs["problem_uuid"] in S.failed_problems:
            response["status"] = "failed"
        else:
            response["status"] = "none"

        return response

    @dispatcher.add_method
    def wipe_memory(**kwargs):
        db_self = MongoClient("mongodb://localhost:27017")
        for c in db_self.ml_results_tmp.list_collection_names():
            db_self.ml_results_tmp[c].drop()

        db_self.mios.problem_knowledge.drop()

    @dispatcher.add_method
    def set_visualizer_url(**kwargs):
        if "url" not in kwargs:
            print("Missing parameter: url")
            return
        global S
        print('Setting visualizer url to ' + kwargs["url"] + ":4000")
        S.set_visualization_url(kwargs['url'])
