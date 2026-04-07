from xmlrpc.client import ServerProxy
from utils.ws_client import call_method
from utils.helper_functions import lowest_results, mean_results, learned_successfull, n_trial_until
from experiments.config import get_ips

def get_states(modules: list) -> list:
    """Check if robot modules are ready (IdleTask and ml_service not busy)."""
    ips = get_ips(modules)
    states = []
    for ip, module in zip(ips, modules):
        print(f"get state of {module}")
        try:
            response = call_method(ip, 12000, "get_state", timeout=3)
        except OSError:
            response = None
        
        if response is None:
            states.append(False)
            continue
            
        try:
            s = ServerProxy(f"http://{ip}:8000", allow_none=True)
            busy = s.is_busy()
            status = response["result"]["current_task"]
            if status == "IdleTask" and not busy:
                states.append(True)
            else:
                states.append(False)
                print(f"  {ip} robot is not ready: ml_service is busy={busy}, mios state={status}")
        except (KeyError, Exception):
            states.append(False)
    return states

def get_cutoff():
    cutoff = {}
    from experiments.config import list_block_1, list_block_2, list_U
    modules = list_block_1 + list_block_2 + list_U
    for xxx in modules:
        ip = get_ips([xxx])[0]
        cost_coll = lowest_results(ip, ["visualization_collective"])
        cost_iso = lowest_results(ip, ["visualization_isolated"])
        cost = min(cost_coll, cost_iso)
        if cost < 0.2:
            cost = max(cost_coll, cost_iso)
        elif max(cost_coll, cost_iso) > 1.5:
            cost = min(cost_coll, cost_iso)
        
        cutoff[f"{xxx}_left"] = float(cost * 1.2)
    return cutoff

def get_successfull_tasks(tags=["baseline", "iteration_0"], tasks_dict=None):
    if tasks_dict is None:
        return {}
    cutoff = {}
    for host, info in tasks_dict.items():
        task_list = info.get("sequence", [])
        for task in task_list:
            try:
                search_tags = tags + [task]
                successes = learned_successfull(host, search_tags)
            except Exception:
                successes = [False]
            cutoff[task] = successes
    return cutoff

def test_cutoff(cutoff):
    from experiments.config import list_block_1, list_block_2, list_U
    lowest_index = {}
    modules = list_block_1 + list_block_2 + list_U
    for xxx in modules:
        ip = get_ips([xxx])[0]
        idx_coll = n_trial_until(ip, ["visualization_collective"], cutoff[f"{xxx}_left"])
        idx_iso = n_trial_until(ip, ["visualization_isolated"], cutoff[f"{xxx}_left"])
        lowest_index[f"{xxx}_left"] = min(idx_coll, idx_iso)
    return lowest_index
