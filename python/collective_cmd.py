from desk.mongodb_client import MongoDBClient
import pymongo
from threading import Thread
from utils.ws_client import call_method

hostnames = ["collective-%03d.rsi.ei.tum.de"%n for n in range(1,25)]

def populate_database(host, db, ip, user_name="franka", user_pw="frankaRSI"):
    try:
        client = MongoDBClient(host)
        new_params = {"desk_name":user_name, "desk_pwd":user_pw,"robot_ip":ip, "spoc_token":"","spoc_in_control":False}
        client.update(db,"parameters",{"name":"system"}, new_params)
        print("updated ", host)
    except:
            print(host, " not updated")
def populate_databases(db, ip, user_name="franka", user_pw="frankaRSI"):
    for host in hostnames:
        populate_database(host,db,ip,user_name,user_pw)

def populate_all():
    threads = []
    for host in hostnames:
        threads.append(Thread(target=populate_database, args=(host,"miosL","192.168.3.100","franka","frankaRSI",)))
        threads[-1].start()
        threads.append(Thread(target=populate_database, args=(host,"miosR","192.168.4.100","franka","frankaRSI",)))
        threads[-1].start()
    
    for t in threads:
        t.join()

def command_collective(cmd: str, args: dict = {}):
    threads = []
    for r in hostnames:
        robot = r
        threads.append(Thread(target=call_method, args=(robot, 12000, cmd, args,)))
        threads.append(Thread(target=call_method, args=(robot, 13000, cmd, args,)))
        threads[-2].start()
        threads[-1].start()

    for t in threads:
        t.join()


