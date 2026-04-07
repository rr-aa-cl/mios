from xmlrpc.client import ServerProxy
from mongodb_client.mongodb_client import MongoDBClient
from utils.ws_client import call_method
from utils.helper_functions import move_joint, move, grasp_insertable, place_insertable
from experiments.config import get_ips

def stop_services(robots: list = ["localhost"]):
    """Stop the ml_service on multiple robot agents."""
    for r in robots:
        s = ServerProxy(f"http://{r}:8000", allow_none=True)
        try:
            s.stop_service()
        except Exception as e:
            print(f"Error with robot {r}: {e}")

def delete_results(robot: str, tags: list):
    """Delete research results from Mongo for a specific robot/tag set."""
    client = MongoDBClient(robot)
    if not client.remove("ml_results", "insertion", {"meta.tags": tags}):
        print(f"Cannot find {tags} at ml_results")
    if not client.remove("local_knowledge", "insertion", {"meta.tags": tags}):
        print(f"Cannot find {tags} at local_knowledge")
    if not client.remove("global_knowledge", "insertion", {"meta.tags": tags}):
        print(f"Cannot find {tags} at global_knowledge")

def delete_some_results(modules: list, tags: list):
    ips = get_ips(modules)
    for ip, module in zip(ips, modules):
        print(f"\nDelete results on {module}")
        delete_results(ip, tags)

def delete_double_results(modules: list, tags: list, keep_newest=True):
    ips = get_ips(modules)
    for ip, module in zip(ips, modules):
        client = MongoDBClient(ip)
        results = client.read("ml_results", "insertion", {"meta.tags": tags})
        if len(results) > 1:
            times = [r["meta"]["t_0"] for r in results]
            if keep_newest:
                keep_this = max(times)
                delete_this = [r["_id"] for r in results if r["meta"]["t_0"] < keep_this]
            else:
                keep_this = min(times)
                delete_this = [r["_id"] for r in results if r["meta"]["t_0"] > keep_this]
            print(f"\nFound multiple results on {module}")
            for id in delete_this:
                client.remove("ml_results", "insertion", {"_id": id})
        else:
            print(f"found {len(results)} results. Nothing to delete.")

def check_pose(robot, pose):
    error = []
    call_method(robot, 12000, "home_gripper")
    move_joint(robot, f"{pose}_container_above")
    call_method(robot, 12000, "home_gripper")
    move_joint(robot, f"{pose}_container_approach")
    move(robot, pose, [0, 0, 0])
    move_joint(robot, pose)
    result = call_method(robot, 12000, "grasp_object", {"object": pose})
    if not result["result"]["result"]:
        print(f"{pose} not working")
        call_method(robot, 12000, "home_gripper")
        error.append(pose)
    else:
        call_method(robot, 12000, "release_object")
    move(robot, f"{pose}_container_approach", [0, 0, 0.06])
    move_joint(robot, f"{pose}_container_above")
    return error

def check_poses(robot_dict):
    error = []
    for robot in robot_dict.keys():
        for pose in robot_dict[robot]:
            e = check_pose(robot, pose)
            if e:
                error.extend(e)
    return error
