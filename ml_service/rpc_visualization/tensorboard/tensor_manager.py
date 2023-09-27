
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import time
import threading
import datetime
import sys
import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer
import json

list_block_1 = ["001", #"002", 
                "003", "004", "005", 
                "006", "007", "008", "010", 
                "011", "012"]
list_block_2 = ["009","013","014","015","016","017",
                "018",#"020",
                "021","022"]
list_U = ["023", "024", "025", "027", "028", "029"
          ] #, "026"
list_external = ["050"]

#robot_list = ["10.157.175.221", "10.157.174.166", "10.157.174.167", "10.157.174.168", "10.157.174.89" , "10.157.174.80" , "10.157.174.200", "10.157.175.129", "10.157.174.36" , "10.157.174.59", "10.157.175.87", "10.157.174.241", "10.157.174.201", "10.157.174.247", "10.157.174.202", "10.157.174.203", "10.157.174.46", "10.157.174.103", "10.157.174.206", "10.157.175.173", "10.157.174.244", "10.157.174.205", "10.157.175.156", "10.157.174.186","10.157.174.245", "10.157.174.249", "10.157.174.255", "10.157.174.42" , "10.157.174.148", "10.157.175.134"]

def get_ips(module_list):
    with open("../../../python/ip.json", "r") as jsonfile:
        data = json.load(jsonfile)        
        ips = [data[i] for i in module_list]
        print(ips)
    return ips

robot_list = get_ips(list_block_1+list_block_2+list_U)


receiving_ip = "10.0.2.32"
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
            print("error")

def send_stop():
    for r in robot_list:
        try:
            server = xmlrpc.client.ServerProxy("http://%s:%s/" %(r, "8000"))
            server.stop_telemetry()
            print(r)
        except:
            print("error")
 

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