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
        self.time_0 = time.time()

        self.server_plotter = None
        self.server_vis = None

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

    def reset_success(self):
        self.cnt_success = 0

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
            if self.flag_stop is True:
                while self.job_queue.qsize() > 0:
                    self.job_queue.get()
                    self.job_queue.task_done()
            continue
            bad_servers = False
            for m in managed_threads:
                if not m["thread"].is_alive():
                    print("LoadBalancer: %s not responding, \
                          removing from server list..." % m["url"])
                    current_servers.remove(m["url"])
                    m["server_ok"] = False
                    bad_servers = True

            if bad_servers:
                cluster_servers = self.get_servers_in_cluster()
                new_servers = list(set(cluster_servers) - set(current_servers))
                for new_url in new_servers:
                    # get failed thread
                    m = next((m for m in managed_threads
                              if m["server_ok"] is False), None)

                    if m is not None:
                        server_list.append(new_url)
                        print("LoadBalancer: Replacing worker thread \
                              %s with %s" % (m["url"], new_url))
                        m["url"] = new_url
                        m["server_ok"] = True
                        t = Thread(target=self._rpc_worker, args=(new_url,))
                        t.daemon = True
                        t.start()
                        m["thread"] = t

    def stop(self):
        self.flag_stop = True

    def _rpc_worker(self, url):
        # worker to handle jobs in queue
        server_ok = True
        while server_ok and self.flag_stop is False:
            job = self.job_queue.get()

            try:
                nominal = False
                while nominal is False:
                    """ do remote procedure call """
                    headers = {'content-type': 'application/json'}
                    payload = {
                        "method": "start_task",
                        "params": job["params"],
                        "jsonrpc": "2.0",
                        "id": job["id"],
                    }
                    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=2000).json()

                    if "unique_task_id" not in response["result"]:
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
                    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=2000).json()

                    try:
                        job["response"] = response["result"]["eval"]
                        job["t_finish"] = time.time()
                        if self.server_plotter is not None:
                            if response["result"]["eval"]["success"]:
                                cost = response["result"]["eval"]['cost_suc']
                            else:
                                print('LOSS')
                                cost = 5 + np.exp(response["result"]["eval"]['cost_err']*100)-1
                                print(cost)
                            self.rpc_call('http://' + self.server_plotter + ':9005','add_value',{'x':time.time() - self.time_0, 'y': cost})
                        if self.server_vis is not None:
                            if response["result"]["eval"]["success"]:
                                cost = response["result"]["eval"]['cost_suc']
                            else:
                                print('LOSS')
                                cost = 5 + np.exp(response["result"]["eval"]['cost_err']*100)-1
                                print(cost)
                            self.rpc_call('http://' + self.server_vis + ':4000','update_visualization',{'params':{'cost':cost,'parameters':job['params'],'robot':url,'success':response["result"]["eval"]["success"]}})

                        nominal = job["response"]["nominal_termination"]
                        nominal = True
                    except KeyError:
                        job["response"] = {"success": False, "cost_suc": 0, "cost_err": 10}
                        job["t_finish"] = time.time()

                self.job_completed.put(job)
                self.job_queue.task_done()
            except (requests.Timeout, requests.ConnectionError):
                # skill server not responding
                server_ok = False
                # put job back into queue
                self.job_queue.put(job)
                self.job_queue.task_done()

    def rpc_call(self, url, method, params):
        """ do remote procedure call """
        headers = {'content-type': 'application/json'}
        payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": 0,
        }
        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=2000).json()
            return response

        except (requests.Timeout, requests.ConnectionError):
            print('Error: Skill server not responding')
            # skill server not responding
            return None
