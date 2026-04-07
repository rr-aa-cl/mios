import json

list_block_1 = ["001", "003", "004", "005", "006", "007", "033", "032", "008"]
list_block_2 = ["035", "034", "013", "014", "015", "042", "017", "016", "021", "022"]
list_U = ["023", "024", "025", "026", "018", "040", "029"]
list_external = ["050"]

def get_ips(module_list):
    with open("../python/ip.json", "r") as jsonfile:
        data = json.load(jsonfile)        
        ips = [data[i] for i in module_list]
    return ips
