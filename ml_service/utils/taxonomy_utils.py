#!/usr/bin/python3 -u
import time
from pymongo import MongoClient
from mongodb_client.mongodb_client import MongoDBClient
from utils.ws_client import *
# from udp_client import *
import logging
import sys
import numpy as np
import copy
import csv


logger = logging.getLogger("skill_test")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


class Task:
    def __init__(self, robot, port=12000):
        self.skill_names = []
        self.skill_types = []
        self.skill_context = dict()
        self.context = {
            "parameters": {
                "skill_names": [],
                "skill_types": [],
                "as_queue": False
            },
            "skills": self.skill_context
        }

        self.robot = robot
        self.port = port
        self.task_uuid = "INVALID"
        self.t_0 = 0

    def add_skill(self, name, skill_class, context):
        self.skill_names.append(name)
        self.skill_types.append(skill_class)
        self.skill_context[name] = context

        self.context["parameters"]["skill_names"] = self.skill_names
        self.context["parameters"]["skill_types"] = self.skill_types
        self.context["skills"] = self.skill_context

    def start(self, queue: bool = False):
        self.t_0 = time.time()
        self.context["parameters"]["as_queue"] = queue
        response = start_task(self.robot, "GenericTask", parameters=self.context, port=self.port)
        self.task_uuid = response["result"]["task_uuid"]

    def wait(self):
        result = wait_for_task(self.robot, self.task_uuid, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result

    def stop(self):
        result = stop_task(self.robot, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result


def teach_object(robot: str, obj: str):
    call_method(robot, 12000, "teach_object", {"object": obj})


def upload_result(host: str, skill_class: str, skill_instance: str, cost_function: str, result: dict):
    db_result = {
        "cost": result["result"]["task_result"]["skill_results"][skill_class]["cost"][cost_function],
        "success": result["result"]["task_result"]["success"]
    }

    client = MongoClient('mongodb://' + host + ':27017')
    performance_data = client.taxonomy.performance
    skill_performance = performance_data.find_one({'name': skill_class})
    found = False
    if skill_performance is None:
        skill_performance = dict()
        skill_performance["results"] = dict()
        skill_performance["name"] = skill_class
    else:
        found = True

    if skill_instance not in skill_performance["results"]:
        skill_performance["results"][skill_instance] = dict()
    if cost_function not in skill_performance["results"][skill_instance]:
        skill_performance["results"][skill_instance][cost_function] = []
    skill_performance["results"][skill_instance][cost_function].append(db_result)

    if found is True:
        performance_data.delete_many({'name': skill_class})

    performance_data.insert_one(skill_performance)


def download_knowldge_to_context(host: str, db: str, skill_class: str, tags: list, context, context_map):
    client = MongoDBClient(host)
    # result_db = client[db]
    # skill_collection = result_db[skill_class]
    # results = skill_collection.find({"meta.tags": {"$all": tags}})
    results = client.read(db,skill_class,{"meta.tags":tags})
    print(len(results),"\n",results)
    theta = results[0]["parameters"]
    
    for p in theta.keys():
        mapping = context_map[p]
        for m in mapping:
            mapping_arr = m.split(".")
            param_arr = mapping_arr[-1].split("-")
            if len(param_arr) == 2:
                context["skill"][mapping_arr[3]][param_arr[0]][int(param_arr[1]) - 1] = theta[p]
            else:
                context["skill"][mapping_arr[3]][param_arr[0]] = theta[p]

    return context

def download_result(host: str, db: str, skill_class: str, uuid: str, trial: int):
    client = MongoClient('mongodb://' + host + ':27017')
    result_db = client[db]
    skill_collection = result_db[skill_class]
    results = skill_collection.find_one({"meta.uuid": uuid})
    trial = results["n" + str(trial)]

    context = results["meta"]["default_context"]["skills"][skill_class]
    context_map = results["meta"]["domain"]["context_mapping"]

    for p in trial["theta"].keys():
        mapping = context_map[p]
        for m in mapping:
            mapping_arr = m.split(".")
            param_arr = mapping_arr[-1].split("-")
            if len(param_arr) == 2:
                context["skill"][mapping_arr[3]][param_arr[0]][int(param_arr[1]) - 1] = trial["theta"][p]
            else:
                context["skill"][mapping_arr[3]][param_arr[0]] = trial["theta"][p]

    return context


def download_result2(host: str, db: str, skill_class: str, task: str, cost_function: str):
    client = MongoClient('mongodb://' + host + ':27017')
    result_db = client[db]
    skill_collection = result_db[skill_class]
    results = skill_collection.find_one({"task": task, "cost_function": cost_function})
    return results["config"]


def copy_result(host_src: str, db_src: str, skill_class: str, uuid: str, trial: int, host_dst: str, db_dst: str,
                task: str, cost_function: str):
    client = MongoClient('mongodb://' + host_src + ':27017')
    result_db = client[db_src]
    skill_collection = result_db[skill_class]
    results = skill_collection.find_one({"meta.uuid": uuid})
    trial = results["n" + str(trial)]
    results_dst = {
        "meta": results["meta"],
        "trial": trial,
        "task": task,
        "cost_function": cost_function
    }

    client_dst = MongoClient('mongodb://' + host_dst + ':27017')
    client_dst[db_dst][skill_class].insert_one(results_dst)


def download_best_result(host: str, db: str, skill_class: str, skill_instance: str, cost_function: str):
    client = MongoClient('mongodb://' + host + ':27017')
    result_db = client[db]
    skill_collection = result_db[skill_class]
    results = skill_collection.find({"meta.skill_instance": skill_instance})
    trials, context_map, default_context = get_successful_trials(results)
    clusters = find_cluster(trials)
    successful_trials = clusters[0]
    for i in range(len(clusters)):
        if len(clusters[i]) > len(successful_trials):
            successful_trials = clusters[i]
    context = default_context["skills"][skill_class]

    for p in successful_trials[0]["theta"].keys():
        mapping = context_map[p]
        for m in mapping:
            mapping_arr = m.split(".")
            param_arr = mapping_arr[-1].split("-")
            if len(param_arr) == 2:
                context["skill"][mapping_arr[3]][param_arr[0]][int(param_arr[1]) - 1] = successful_trials[0]["theta"][p]
            else:
                context["skill"][mapping_arr[3]][param_arr[0]] = successful_trials[0]["theta"][p]
    return context

def download_best_result_tags(host: str, db: str, skill_class: str,  tags: list):
    client = MongoClient('mongodb://' + host + ':27017')
    result_db = client[db]
    skill_collection = result_db[skill_class]
    results = skill_collection.find({"meta.tags": {"$all":tags}})
    trials, context_map, default_context = get_successful_trials(results)
    clusters = find_cluster(trials)
    trials.sort(key=lambda t: t["q_metric"]["final_cost"])
    successful_trials = clusters[0]  # trials

    context = default_context["skills"][skill_class]

    for p in successful_trials[0]["theta"].keys():
        mapping = context_map[p]
        for m in mapping:
            mapping_arr = m.split(".")
            param_arr = mapping_arr[-1].split("-")
            if len(param_arr) == 2:
                context["skill"][mapping_arr[3]][param_arr[0]][int(param_arr[1]) - 1] = successful_trials[0]["theta"][p]
            else:
                context["skill"][mapping_arr[3]][param_arr[0]] = successful_trials[0]["theta"][p]
    return context

def download_best_result_2(host: str, db: str, skill_class: str, skill_instance: str, cost_function: str):
    client = MongoClient('mongodb://' + host + ':27017')
    result_db = client[db]
    skill_collection = result_db[skill_class]
    results = skill_collection.find({"meta.skill_instance": skill_instance})
    trials, context_map, default_context = get_successful_trials(results)
    best_trial = {}
    best_cost = 10000
    for t in trials:
        if t["q_metric"]["final_cost"] < best_cost:
            best_trial = t
            best_cost = t["q_metric"]["final_cost"]
        context = default_context["skills"][skill_class]

    for p in best_trial["theta"].keys():
        mapping = context_map[p]
        for m in mapping:
            mapping_arr = m.split(".")
            param_arr = mapping_arr[-1].split("-")
            if len(param_arr) == 2:
                context["skill"][mapping_arr[3]][param_arr[0]][int(param_arr[1]) - 1] = best_trial["theta"][p]
            else:
                context["skill"][mapping_arr[3]][param_arr[0]] = best_trial["theta"][p]

    return context


def get_successful_trials(doc):
    meta_info = []
    successful_trials = []
    for d in doc:
        meta_info.append(d["meta"])
        # get raw ml data:
        trials = get_raw_data(d)
        for t in trials:
            successful_trials.append(t)

    context_map = meta_info[0]["domain"]["context_mapping"]
    default_context = meta_info[0]["default_context"]
    return successful_trials, context_map, default_context


def get_raw_data(d):
    successful_trials = []
    for nr in range(len(d)):
        key = "n" + str(nr)
        if d.get(key, False):  # if trial number available
            if d[key]["q_metric"]["success"]:  # if trial was successful
                successful_trials.append(d[key])
    return successful_trials


def find_cluster(data):
    def distance_to(a, b):
        """distance between 2 multidimensional points"""
        return np.sqrt(sum((np.array(a) - np.array(b)) ** 2))

    data = copy.deepcopy(data)
    logger.debug("ClusterProcessor: start working")
    clusters = []

    while data:
        # sort for cost
        c_list = sorted(data, key=lambda t: (t["q_metric"]["final_cost"]))  # lowest cost first
        # sorted for distance to best trial:
        d_list = sorted(data, key=lambda t: distance_to(dict_to_list(t["theta"]),
                                                        dict_to_list(c_list[0]["theta"])))
        cluster = [data.pop(data.index(d_list[0]))]
        for d_trial in d_list[1:]:
            mean_gradient = 0
            if len(cluster) >= 2:
                for trial in cluster[1:]:
                    mean_gradient += (trial["q_metric"]["final_cost"] - cluster[0]["q_metric"][
                        "final_cost"]) / distance_to(dict_to_list(trial["theta"]), dict_to_list(cluster[0]["theta"]))
                mean_gradient = mean_gradient / len(cluster[1:])

            dist = distance_to(dict_to_list(d_trial["theta"]), dict_to_list(cluster[0]["theta"]))

            if d_trial["q_metric"]["final_cost"] > cluster[-1]["q_metric"]["final_cost"]:
                cluster.append(data.pop(data.index(d_trial)))
            elif d_trial["q_metric"]["final_cost"] > 0.8 * dist * mean_gradient + cluster[0]["q_metric"]["final_cost"]:
                cluster.append(data.pop(data.index(d_trial)))
            else:
                break

        clusters.append(cluster)

    return clusters


def dict_to_list(d):
    """returns a list with dict contents"""
    l = []
    for key in d.keys():
        l.append(d[key])
    return l


def create_result_table(host: str, db: str):
    client = MongoClient('mongodb://' + host + ':27017')
    result_db = client[db]
    performance_docs = result_db.performance.find({})
    skills = dict()
    for doc in performance_docs:
        skills[doc["name"]] = dict()
        for s in doc["results"].keys():
            robustness = 0
            cost = 0
            for r in doc["results"][s]:
                robustness += int(r["success"])
                cost += r["cost"]["time"]

            skills[doc["name"]][s] = {
                "robustness": robustness / len(doc["results"][s]),
                "cost": cost / len(doc["results"][s])
            }

    print(skills)
    f = open('performance_table.csv', 'w')
    writer = csv.writer(f)
    header_row = ["Skill Class", "Skill Instance", "Robustness", "Execution Time"]
    writer.writerow(header_row)
    for s in skills.keys():
        for si in skills[s].keys():
            row = [s, si, skills[s][si]["robustness"], skills[s][si]["cost"]]
            writer.writerow(row)


def read_data(host: str, skill_class: str, skill_instance: str, cost_function: str):
    client = MongoClient('mongodb://' + host + ':27017')
    doc = client.taxonomy.performance.find_one({"name": skill_class})
    results = doc["results"][skill_instance][cost_function]
    success_rate = 0
    n_total_results = len(results)
    n_success_results = 0
    cost = 0
    cost2 = []
    for r in results:
        if r["success"] is True:
            success_rate += 1
            n_success_results += 1
            cost += r["cost"]
            cost2.append(r["cost"])

    cost_std = np.std(cost2)
    z = 0.475
    ci = z * cost_std / np.sqrt(len(cost2))
    success_rate /= n_total_results
    cost /= n_success_results

    print("Success rate: " + str(success_rate) + ", cost: " + str(cost) + " +- " + str(ci))


def ask_for_result(result):
    while True:
        text = input("Successful? (y/n)")
        if text == "y":
            success = True
            break
        elif text == "n":
            success = False
            break
        else:
            print("False input.")
            continue
    result["result"]["task_result"]["success"] = success
