import requests
import getpass
import json
from subprocess import check_output, CalledProcessError, STDOUT
from time import sleep
import xmlrpc.client as cl
from http.client import CannotSendRequest
from http.client import ResponseNotReady

from threading import Thread
from queue import Queue
import time
import numpy as np


class LoadBalancer(object):
    """Class to handle load balancing for parallel learning with rpc"""

    def __init__(self, rpc_url=["http://localhost:8383"]):
        self.job_queue = Queue()
        self.job_completed = Queue()
        self.flag_stop = False
        self.flag_pause = False
        self.time_0 = time.time()

        self.visualization_url = None

        rpc_servers = []

        if len(rpc_servers) == 0:
            rpc_servers = rpc_url

        print("LoadBalancer: Starting worker manager thread")
        if rpc_url is not None:
            t = Thread(target=self._worker_manager, args=(rpc_servers,))
            t.daemon = True
            t.start()
        else:
            print('No url specified, doing nothing.')

    def set_visualization_url(self, url):
        self.visualization_url = url

    def _worker_manager(self, server_list):
        """ thread to manage worker threads """
        managed_threads = []
        current_servers = server_list

        # start worker threads
        for url in server_list:
            print("LoadBalancer: Starting worker thread for %s" % url)
            t = Thread(target=self._rpc_worker, args=(url,))
            t.daemon = True
            t.start()
            managed_threads.append({"thread": t, "url": url,
                                    "server_ok": True})

        # monitor worker threads
        while self.flag_stop is False:
            sleep(1)
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

    def stop(self):
        self.flag_stop = True

    def pause(self, pause_state):
        self.flag_pause = pause_state

    def _rpc_worker(self, url):
        # worker to handle jobs in queue
        server_ok = True
        while server_ok and self.flag_stop is False:
            job = self.job_queue.get()

            try:
                nominal = False
                while nominal is False:
                    """ do remote procedure call """
                    repeat = True
                    cnt_repeat = 0
                    while repeat is True and self.flag_stop is False:
                        if self.flag_pause is True:
                            print("Service is paused.")
                            time.sleep(1)
                            continue
                        headers = {'content-type': 'application/json'}
                        payload = {
                            "method": "start_task",
                            "params": job["params"],
                            "jsonrpc": "2.0",
                            "id": job["id"],
                        }
                        print(url)
                        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=2000).json()

                        if response is None or "unique_task_id" not in response["result"]:
                            print("Task could not be started on target robot with url "+url+". Retrying after 1 second...")
                            time.sleep(1)
                            continue

                        payload = {
                            "method": "wait_for_task",
                            "params": {
                                "unique_task_id": response["result"]["unique_task_id"]
                            },
                            "jsonrpc": "2.0",
                            "id": job["id"],
                        }
                        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=20000).json()
                        print(response["result"]["eval"])
                        if response["result"]["eval"]["error"] != "control_exception":
                            repeat = False
                            cnt_repeat = 0
                        else:
                            cnt_repeat +=1
                            print("REPEAT")

                        if cnt_repeat > 5:
                            repeat = False

                        if response is None:
                            print('Lost connection to MIOS core.')
                            return

                        try:
                            job["response"] = response["result"]["eval"]
                            job["t_finish"] = time.time()
                            nominal = job["response"]["nominal_termination"]
                            nominal = True
                            if self.visualization_url is not None:
                                if response["result"]["eval"]["success"]:
                                    cost = response["result"]["eval"]['cost_suc']
                                else:
                                    cost = 5 + np.exp(response["result"]["eval"]['cost_err'] * 100) - 1
                                self.rpc_call('http://' + self.visualization_url + ':4000', 'update_visualization', {
                                    'params': {'cost': cost, 'parameters': job['params'], 'robot': url,
                                               'success': response["result"]["eval"]["success"]}}, timeout=1)

                        except KeyError:
                            job["response"] = {"success": False, "cost_suc": 0, "cost_err": 0}
                            job["t_finish"] = time.time()

                        # RESET INSTRUCTIONS
                        if 'reset_instructions' not in job:
                            print('Problem definition does not contain reset instructions, aborting...')
                            return

                        task_list = job["reset_instructions"]["tasks"]

                        for t in task_list:
                            if t not in job["reset_instructions"]:
                                print('Task ' + t + ' was declared in the reset instructions but not defined.')
                                return

                            headers = {'content-type': 'application/json'}
                            params = job["reset_instructions"][t]

                            while True:
                                if self.flag_pause is True:
                                    print("Service is paused.")
                                    time.sleep(1)
                                    continue
                                params["task_id"] = t
                                payload = {
                                    "method": "start_task",
                                    "params": params,
                                    "jsonrpc": "2.0",
                                    "id": 0,
                                }
                                response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=40000).json()

                                if response is None or "unique_task_id" not in response["result"]:
                                    print("Task could not be started on target robot with url " + url + ". Retrying after 1 second...")
                                    time.sleep(1)
                                    continue

                                payload = {
                                    "method": "wait_for_task",
                                    "params": {
                                        "unique_task_id": response["result"]["unique_task_id"]
                                    },
                                    "jsonrpc": "2.0",
                                    "id": job["id"],
                                }
                                response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=40000).json()
                                if response["result"]["eval"]["error"] != "control_exception":
                                    break

                self.job_completed.put(job)
                self.job_queue.task_done()
            except (requests.Timeout, requests.ConnectionError):
                # skill server not responding
                server_ok = False
                # put job back into queue
                self.job_queue.put(job)
                self.job_queue.task_done()

    def rpc_call(self, url, method, params, timeout=2000):
        """ do remote procedure call """
        headers = {'content-type': 'application/json'}
        payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": 0,
        }
        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=timeout).json()

        except requests.Timeout:
            print('Timeout, server has terminated or does not exist.')
            response = None
        except requests.ConnectionError:
            print('Connection error, target url not reachable.')
            response = None
        return response