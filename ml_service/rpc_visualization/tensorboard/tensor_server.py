# tensorboard depends
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import time
import threading
import datetime
import sys
import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer
import argparse
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from threading import Thread
from tempfile import TemporaryFile
from copy import deepcopy



# writer = SummaryWriter(log_dir= "x11x/collective_" + datetime.datetime.now().strftime("%d%b-%H:%M") , flush_secs=1) 
list_block_1 = ["001", #"002", 
                "003", "004", "005", 
                "006", "007", " ", "010", 
                "011", "012"]
list_block_2 = ["009","013","014","015","016","017",
                # "018",#"020",
                "041",
                "021","022"]
list_U = ["023", "024", "025", "027", "028", "029"] #, "026"
list_external = ["050"]
modules = list_block_1+list_block_2+list_U
print(modules)


class Server(): 
    def __init__(self, server_addr): 
        print(server_addr)
        print(type(server_addr))
        self.writer = SummaryWriter(log_dir= "x00x/collective_" + datetime.datetime.now().strftime("%d%b-%H:%M") , flush_secs=1)
        self.server = SimpleXMLRPCServer((server_addr), allow_none=True) 
        self.save_frame_thread = Thread(target=self.save_frames, args=(100,))
        self.current_data = {}
        self.data_map = {}
        # self.server.register_multicall_functions() 
        self.server.register_function(self.plot, 'plot') 
        self.server.register_function(self.echo, 'echo') 
        self.server.register_function(self.plot_old, 'plot_old') 
        self.server.register_function(self.stop, "stop")
        self.storage = []
        self.transfermap_storage = []
        self.current_transfer_data = {}
        self.keep_running = False

        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.save_frame_thread.start()
    
    def stop(self):
        self.keep_running = False
        self.save_frame_thread.join()
        

    def plot(self, hostname, data, count):
        #print(hostname,"\n",data, "\n", count)
        external = data["external"]  # False or str
        if external:
            external = external["skill_instance"][:3]  # eg.: "003"
        cost = data["task_result"]["q_metric"]["final_cost"]  #float
        success = data["task_result"]["q_metric"]["success"]
        trial_number = data["trial_number"]  #int 
        #self.writer.add_scalar('Collective Learning/'+hostname, cost, trial_number)
        with self.lock:
            if hostname not in self.current_data.keys():
                self.current_data[hostname] = 0
            elif success:
                self.current_data[hostname] += 1 

            if hostname not in self.current_transfer_data.keys():
                self.current_transfer_data[hostname] = {}
            if external:
                if external not in self.current_transfer_data[hostname].keys():
                    #self.current_transfer_data[hostname][external] = 0
                    self.current_transfer_data[hostname][external] = 3  #float("inf")
                if success:
                    #self.current_transfer_data[hostname][external] += 1
                    if cost < self.current_transfer_data[hostname][external]:
                        self.current_transfer_data[hostname][external] = cost
                else:
                    #self.current_transfer_data[hostname][external] -= 1
                    if cost < self.current_transfer_data[hostname][external]:
                        self.current_transfer_data[hostname][external] = cost
            else:
                if hostname[-3:] not in self.current_transfer_data[hostname].keys():
                    #self.current_transfer_data[hostname][hostname[-3:]] = 0
                    self.current_transfer_data[hostname][hostname[-3:]] = 3
                if success:
                    #self.current_transfer_data[hostname][hostname[-3:]] += 1
                    if cost < self.current_transfer_data[hostname][hostname[-3:]]:
                        self.current_transfer_data[hostname][hostname[-3:]] = cost
                else:
                    #self.current_transfer_data[hostname][hostname[-3:]] += 1
                    if cost < self.current_transfer_data[hostname][hostname[-3:]]:
                        self.current_transfer_data[hostname][hostname[-3:]] = cost
        #self.plotter.add_data(hostname, cost)

    def save_frames(self, period):
        self.keep_running = True
        current_heatmap = np.zeros((5,5))
        current_transfermap = np.ones((25,25)) * 3
        while self.keep_running:
            with self.lock:
                for name in self.current_data.keys():  # name = hostname like "collective-003"
                        index = modules.index(name[-3:])
                        col = index%5
                        row = int(index/5)
                        current_heatmap[row][col] = self.current_data[name]
                        for knowledge_source in self.current_transfer_data[name].keys():  # knowledge_source like "003"
                            current_transfermap[modules.index(knowledge_source)][modules.index(name[-3:])] = self.current_transfer_data[name][knowledge_source]
            print("number of sumbmitted agents: ", len(self.current_data.keys()))
            self.storage.append(deepcopy(current_heatmap))
            self.transfermap_storage.append(deepcopy(current_transfermap))
            np.save("heatmap_alpha_5_reverse.npy", self.storage)
            np.save("transfermap_alpha_5_reverse.npy",self.transfermap_storage)
            time.sleep(period/1000)
        print("storing data done")

    def plot_old(self, plot_name:str, data:float, n):
        print((plot_name, data, n))
        self.writer.add_scalar('Collective Learning/' + plot_name, data, n)
        print("print data", n)
        return (plot_name, data, n)
        
    def echo(self,x):
        print(x)
 
    def start(self): 
        print ("Server thread started. Testing the server...") 
        self.server.serve_forever() 
        
    def stop_server(self):
        self.keep_running = False
        self.save_frame_thread.join()
        self.server.server_close()
        self.server.shutdown()
        print("Tensorboard server stop")
        
# lsof -i tcp:7000
# @timeout_decorator.timeout(3)
# def start_visual():
#     proxy = xmlrpc.client.ServerProxy("http://%s:%s/" %("localhost", "8000"))        
#     proxy.start_visualization("localhost", 8002)

if __name__ == '__main__': 
    try:
        # ------------------- start rpc_vis server -----------------------
        server_addr = ("10.157.175.246", 8004) 
        server = Server(server_addr) 
        server.start()
        #t = threading.Thread(target=server.start)
        #t.start()  
        # ------------------- start rpc_vis server -----------------------
        
        # robot_list = ["10.157.174.205"]
        
        
        # proxy = xmlrpc.client.ServerProxy("http://%s:%s/" %("10.157.174.205", "8002"))
        
        # proxy.send_start()
        # time.sleep(5)
        # proxy.send_off()
        # proxy.empty_buffer()
        # proxy.start_visualization("10.157.175.142", 8002)
        
        # robots_dualarm = ["10.157.174.205", "10.157.175.156"]
        # proxy_list = []
        # thread_list = []
        
        # proxy = xmlrpc.client.ServerProxy("http://%s:%s/" %(robots_dualarm[0], "8000"))
        # proxy.start_visualization("10.157.175.142", 8002)
        
        
        # # for i in range(len(robots_dualarm)):
        #     proxy_list.append(xmlrpc.client.ServerProxy("http://%s:%s/" %(robots_dualarm[i], "8000")))
        #     thread_list.append(threading.Thread(target=proxy_list[i].start_visualization, args=("10.157.175.142", 8002)))
        #     print(i)
                        
        # for thread in thread_list:
        #     thread.start()
        
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        # for thread in thread_list:
        #     thread.join()

        # proxy = xmlrpc.client.ServerProxy("http://%s:%s/" %("10.157.175.142", "8000"))  
        # proxy.start_visualization("10.157.175.142", 8002)
        # print("xxxxxxxxxxxxxxxxxxxxxx")
        # ------------------- start rpc_vis server -----------------------

        #t.join()
        
    except KeyboardInterrupt:
        server.stop_server()
        sys.exit(0)


# Name: torch
# Version: 1.13.1+cpu
# Summary: Tensors and Dynamic neural networks in Python with strong GPU acceleration
# Home-page: https://pytorch.org/
# Author: PyTorch Team
# Author-email: packages@pytorch.org
# License: BSD-3
# Location: /home/popnut/.local/lib/python3.8/site-packages
# Requires: typing-extensions
# Required-by: torchvision, torchaudio

# tensorboard --logdir x00x
