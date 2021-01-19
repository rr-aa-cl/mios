from utils.experiment_wizard import start_experiment
from definitions.insertion_definitions import insert_cylinder
from definitions.insertion_definitions import insert_cylinder_light
from definitions.insertion_definitions import insert_key
from definitions.insertion_definitions import insert_key_light
from definitions.insertion_definitions import insert_generic
from definitions.benchmark_definitions import mios_ml_benchmark
from services.cmaes import CMAESConfiguration
from utils.udp_client import call_method
from utils.database import delete_local_results
from utils.database import delete_local_knowledge
from experiments.collective_learning import CollectiveLearningBase


def simple_benchmark():
    pd = mios_ml_benchmark()
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-007.local", pd, service_config, 3)


def transfer_learning_debug(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    pd = insert_cylinder(10)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("localhost", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_benchmark_1(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    pd = mios_ml_benchmark(0)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 20
    pd.cost_function.optimum_weights[1] = 1
    pd.cost_function.optimum_weights[2] = 0
    delete_local_results(["localhost"], "benchmark_rastrigin", ["transfer_learning", "shift_0"])
    delete_local_knowledge(["localhost"], "benchmark_rastrigin", ["transfer_learning", "shift_0"])
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("localhost", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_benchmark_2(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    pd = mios_ml_benchmark(1)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 20
    pd.cost_function.optimum_weights[1] = 0
    pd.cost_function.optimum_weights[2] = 1
    knowledge = None
    delete_local_results(["localhost"], "benchmark_rastrigin", ["transfer_learning", "shift_1"])
    delete_local_knowledge(["localhost"], "benchmark_rastrigin", ["transfer_learning", "shift_1"])
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("localhost", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_10(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-007.local", 12002, "set_grasped_object", {"object": "cylinder_10"})
    pd = insert_cylinder(10)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-007", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_20(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-007.local", 12002, "set_grasped_object", {"object": "cylinder_20"})
    pd = insert_cylinder(20)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-007", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_30(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-008.local", 12002, "set_grasped_object", {"object": "cylinder_30"})
    pd = insert_cylinder(30)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-008", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_40(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-001.local", 12002, "set_grasped_object", {"object": "cylinder_40"})
    pd = insert_cylinder(40)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-001", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_50(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-001.local", 12002, "set_grasped_object", {"object": "cylinder_50"})
    pd = insert_cylinder(50)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-001", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_60(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-008.local", 12002, "set_grasped_object", {"object": "cylinder_60"})
    pd = insert_cylinder(60)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-008", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_abus_e30(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-002.local", 12002, "set_grasped_object", {"object": "key_abus_e30"})
    pd = insert_key_light("abus_e30")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-002", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_pad_lock(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-009.local", 12002, "set_grasped_object", {"object": "key_pad"})
    pd = insert_key("pad")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-009", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_old_key(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-009.local", 12002, "set_grasped_object", {"object": "key_old"})
    pd = insert_key("old")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-009", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_hatch_key(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-002.local", 12002, "set_grasped_object", {"object": "key_hatch"})
    pd = insert_key("hatch")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
        tags = ["transfer_learning", "from_" + from_tag]
    start_experiment("collective-panda-002", pd, service_config, 10, tags=tags, knowledge=knowledge)


tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60",
         "key_pad", "key_old", "key_hatch"]


def transfer_learning_cylinder_10_t():
    for t in tasks:
        transfer_learning_10("collective-control-001", "transfer_base_v2", "insert_object", t)


def transfer_learning_cylinder_20_t():
    for t in tasks:
        transfer_learning_20("collective-control-001", "transfer_base_v2", "insert_object", t)


def transfer_learning_cylinder_30_t():
    for t in tasks:
        transfer_learning_30("collective-control-001", "transfer_base_v2", "insert_object", t)


def transfer_learning_cylinder_40_t():
    for t in tasks:
        transfer_learning_40("collective-control-001", "transfer_base_v2", "insert_object", t)


def transfer_learning_cylinder_50_t():
    for t in tasks:
        transfer_learning_50("collective-control-001", "transfer_base_v2", "insert_object", t)


def transfer_learning_cylinder_60_t():
    for t in tasks:
        transfer_learning_60("collective-control-001", "transfer_base_v2", "insert_object", t)


def transfer_learning_key_abus_e30_t():
    for t in tasks:
        transfer_learning_abus_e30("collective-control-001", "transfer_base_v2", "insert_object", t)


def transfer_learning_key_hatch_t():
    for t in tasks:
        transfer_learning_hatch_key("collective-control-001", "transfer_base_v2", "insert_object", t)


def transfer_learning_pad_t():
    for t in tasks:
        transfer_learning_pad_lock("collective-control-001", "transfer_base_v2", "insert_object", t)


def transfer_learning_key_old_t():
    for t in tasks:
        transfer_learning_old_key("collective-control-001", "results_tl_base", "insert_object", t)


def transfer_learning_test_20(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-007.local", 12002, "set_grasped_object", {"object": "cylinder_20"})
    pd = insert_cylinder_light(20)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning_test"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning_test", from_tag]
        }
        tags = ["transfer_learning_test", "from_" + from_tag]
    start_experiment("collective-panda-007", pd, service_config, 10, tags=tags, knowledge=knowledge)


def transfer_learning_test_40(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-001.local", 12002, "set_grasped_object", {"object": "cylinder_40"})
    pd = insert_cylinder_light(40)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning_test"]
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning_test", from_tag]
        }
        tags = ["transfer_learning_test", "from_" + from_tag]
    start_experiment("collective-panda-001", pd, service_config, 10, tags=tags, knowledge=knowledge)


def pinakothek(use_prior: bool = False):
    call_method("collective-panda-prime.local", 12002, "set_grasped_object", {"object": "key_old"})
    pd = insert_key("old")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 5
    service_config.n_gen = 10
    knowledge = None
    tags = ["transfer_learning"]
    if use_prior is True:
        knowledge = {
            "mode": "specific",
            "kb_location": "collective-control-001.local",
            "kb_db": "results_tl_base",
            "kb_task_type": "insert_object",
            "kb_tags": ["transfer_learning", "key_old"]
        }
        tags = ["transfer_learning", "from_cylinder_10"]
    start_experiment("collective-panda-prime", pd, service_config, 10, tags=tags, knowledge=knowledge)


def collective_learning_raw():
    call_method("collective-panda-001", 12002, "set_grasped_object", {"object": "generic_insertable"})
    call_method("collective-panda-002", 12002, "set_grasped_object", {"object": "generic_insertable"})
    call_method("collective-panda-007", 12002, "set_grasped_object", {"object": "generic_insertable"})
    call_method("collective-panda-008", 12002, "set_grasped_object", {"object": "generic_insertable"})
    call_method("collective-panda-009", 12002, "set_grasped_object", {"object": "generic_insertable"})
    agents = ["collective-panda-001", "collective-panda-002", "collective-panda-007", "collective-panda-008",
              "collective-panda-009"]

    pd = insert_generic()
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["collective_learning_multi_agent"]
    start_experiment("collective-panda-001", agents, pd, service_config, 10, tags=tags, knowledge=knowledge)
