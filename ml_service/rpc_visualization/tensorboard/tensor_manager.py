
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import time
import threading
import datetime
import sys
import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer
import json
from threading import Thread

list_block_1 = ["001", #"002", 
                "003", "004", "005", 
                "006", "007", "008", "010", 
                "011", "012"]
list_block_2 = ["009","013","014","015","016","017",
                # "018",#"020",
                "041",
                "021","022"]
list_U = ["023", "024", "025", "027", "028", "029"] #, "026"
list_external = ["050"]



def get_ips(module_list):
    with open("../../../python/ip.json", "r") as jsonfile:
        data = json.load(jsonfile)        
        ips = [data[i] for i in module_list]
        print(ips)
    return ips

robot_list = get_ips(list_block_1+list_block_2+list_U)


receiving_ip = "10.157.175.246" # "10.0.2.32"
receiving_port = 8004

def send_start():
    for r in robot_list:
        try: 
            server = xmlrpc.client.ServerProxy("http://%s:%s/" %(r, "8000"))
            result = server.start_telemetry(receiving_ip,receiving_port)
            if not result:
                print("subscribe to telemetry failed for ", r)
            else:
                print("successfully subscribed to ",r)
        except:
            print("communication error with", r)

def send_stop():
    def stop(r):
        try:
            server = xmlrpc.client.ServerProxy("http://%s:%s/" %(r, "8000"))
            server.stop_telemetry()
            print("stop ",r)
        except:
            print("error for ",r)
    threads = []
    for r in robot_list:
        threads.append(Thread(target=stop, args=(r,)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
 

def empty_buffer():
    print("not implemented")
    #for r in robot_list:
    #   try:
    #        server = xmlrpc.client.ServerProxy("http://%s:%s/" %(r, "8000"))
    #        server.empty_buffer()
    #    except:
    #        print("error")

        
def print_all():
    for r in robot_list:
        
        print(r)