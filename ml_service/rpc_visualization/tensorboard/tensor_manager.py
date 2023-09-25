
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import time
import threading
import datetime
import sys
import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer

# robot_list = ["10.157.174.205", "10.157.174.36", "10.157.174.244", "10.157.175.173", "10.157.174.241", "10.157.174.201", "10.157.174.202", "10.157.174.203", "10.157.174.46", "10.157.175.156",
            #   "10.157.174.186", "10.157.174.249", "10.157.174.255", "10.157.174.42"]

robot_list = ["10.157.175.221", "10.157.174.166", "10.157.174.167", "10.157.174.168", "10.157.174.89" , "10.157.174.80" , "10.157.174.200", "10.157.175.129", "10.157.174.36" , "10.157.174.59", "10.157.175.87", "10.157.174.241", "10.157.174.201", "10.157.174.247", "10.157.174.202", "10.157.174.203", "10.157.174.46", "10.157.174.103", "10.157.174.206", "10.157.175.173", "10.157.174.244", "10.157.174.205", "10.157.175.156", "10.157.174.186","10.157.174.245", "10.157.174.249", "10.157.174.255", "10.157.174.42" , "10.157.174.148", "10.157.175.134"]

def send_start():
    for r in robot_list:
        try: 
            server = xmlrpc.client.ServerProxy("http://%s:%s/" %(r, "8002"))
            server.send_start()
            print(r)
        except:
            print("error")

def send_stop():
    for r in robot_list:
        try:
            server = xmlrpc.client.ServerProxy("http://%s:%s/" %(r, "8002"))
            server.send_off()
            print(r)
        except:
            print("error")
 

def empty_buffer():
    for r in robot_list:
        try:
            server = xmlrpc.client.ServerProxy("http://%s:%s/" %(r, "8002"))
            server.empty_buffer()
        except:
            print("error")

        
def print_all():
    for r in robot_list:
        
        print(r)