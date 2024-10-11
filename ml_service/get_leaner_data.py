from mongodb_client.mongodb_client import MongoDBClient


## possible tags:     
tags = ["convergence_test_10.3"]    # new robot oritation, tabletop insertion, freshly teached, origPSP, gmm with 8 components
# tags = ["convergence_test_10.2"]    # new robot oritation, tabletop insertion, freshly teached, origPSP, 
# tags = ["convergence_test_9"]                       # tabletop insertion, freshly teached, origPSP, 
# tags = ["convergence_test_7"]                       # dualarm insertion, lifted joint impedance hold pose, origPSP
# tags = ["convergence_test_6", "holdpose"]           # dualarm insertion, cartesian impedance hold pose with contact to table, origPSP
# tags = ["convergence_test_6", "jointpose"]          # dualarm insertion, joint impedance hold pose with contact to table, origPSP
# tags = ["convergence_test_3"]                       # dualarm insertion, move to hold position, CMAES

## possible hosts:
host = "collective-001.rsi.ei.tum.de"
# host = "collective-003.rsi.ei.tum.de"
# host = "collective-004.rsi.ei.tum.de"
# host = "collective-005.rsi.ei.tum.de"
# host = "collective-006.rsi.ei.tum.de"
# host = "collective-007.rsi.ei.tum.de"
# host = "collective-008.rsi.ei.tum.de"
# host = "collective-011.rsi.ei.tum.de"
# host = "collective-012.rsi.ei.tum.de"
# host = "collective-014.rsi.ei.tum.de"
# host = "collective-015.rsi.ei.tum.de"
# host = "collective-017.rsi.ei.tum.de"
# host = "collective-021.rsi.ei.tum.de"
# host = "collective-022.rsi.ei.tum.de"
# host = "collective-023.rsi.ei.tum.de"
# host = "collective-024.rsi.ei.tum.de"
# host = "collective-025.rsi.ei.tum.de"
# host = "collective-026.rsi.ei.tum.de"
# host = "collective-027.rsi.ei.tum.de"
# host = "collective-042.rsi.ei.tum.de"
# host = "collective-043.rsi.ei.tum.de"
# host = "collective-044.rsi.ei.tum.de"
# host = "collective-047.rsi.ei.tum.de"

def request_data(host, tags):
    client = MongoDBClient(host)
    data = client.read("ml_results","insertion",{"meta.tags":tags})
    if len(data) == 0:
        print("no data found on ", host)
        return False
    if len(data) > 1:
         print("multiple ml runs found. taking most recent one")
         data = data[-1:]
    return data[0]

data = request_data(host, tags)
if not data:
    print("No data found")
thetas = []
costs = []
for key in data.keys():
    if key[0] != "n":
        continue
    thetas.append(data[key]["theta"])
    costs.append(data[key]["q_metric"]["final_cost"])

print(costs)

print(thetas)
