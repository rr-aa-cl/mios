from desk.mongodb_client import MongoDBClient
import pymongo


hostnames = ["collective-%03d.rsi.ei.tum.de"%n for n in range(1,51)]

def populate_databases(db, ip, user_name="franka", user_pw="frankaRSI"):
    for host in hostnames:
        print(host)
        try:
            client = MongoDBClient(host)
            new_params = {"desk_name":user_name, "desk_pwd":user_pw,"robot_ip":ip}
            client.update(db,"parameters",{"name":"system"}, new_params)
            print("updated ", host, "with ", new_params)
        except KeyboardInterrupt:
            break
        except:
            print(host, " not updated")



