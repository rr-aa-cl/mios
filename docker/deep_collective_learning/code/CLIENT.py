import xmlrpc.client
import time
import os
import json

list_block_1 = ["001", #"002", 
                "003", "004", "005", 
                "006", "007", "008", "010", 
                "011", "012"]
list_block_2 = ["009","013","014","015","016","017",
                # "018",#"020",
                "041",
                "021","022"]
list_U = ["023", "024", "025", "026", "027", "029"] 
list_external = ["050"]

def get_ips(module_list):
    with open("../../../python/ip.json", "r") as jsonfile:
        data = json.load(jsonfile)        
        ips = [data[i] for i in module_list]
        print(ips)
    
    return ips
modules = list_block_1+ list_block_2 + list_U
# modules = ["026"]
ips = get_ips(modules)

for ip in ips:
    try:
        with xmlrpc.client.ServerProxy("http://" + ip + ":9000") as s:
            s.start_recording("HelloWorld")
            time.sleep(5)
            s.stop_recording()
            print("done:  " + ip)
    except:
        print("error: oooooooooooooooooo " + ip)

# sudo v4l2-ctl --list-devices 

# adm?-Dualarm
# sudo apt install v4l-utils -y/dev


