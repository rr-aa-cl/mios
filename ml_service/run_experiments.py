from utils.experiment_wizard import *
from definitions.insertion_definitions import insert_cylinder
from definitions.insertion_definitions import insert_cylinder_light
from definitions.insertion_definitions import insert_key
from definitions.insertion_definitions import insert_key_light
from definitions.insertion_definitions import insert_generic
from definitions.benchmark_definitions import mios_ml_benchmark
from definitions.templates import move
from definitions.templates import turn
from definitions.templates import tax_insertion
from definitions.templates import press_button
from definitions.templates import extraction
from definitions.templates import place
from definitions.templates import grab
from services.cmaes import CMAESConfiguration
from services.svm import SVMConfiguration
from utils.udp_client import call_method
from utils.database import delete_local_results
from utils.database import delete_local_knowledge
from utils.database import backup_results
from experiments.collective_learning import CollectiveLearningBase

from threading import Thread
from xmlrpc.client import ServerProxy


def simple_benchmark(robot: str, agents: list, n_iter: int = 1, tags: list = []):
    pd = mios_ml_benchmark(0.2)
    #service_config = CMAESConfiguration()
    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    #service_config.n_ind = 10
    #service_config.n_gen = 10
    service_config.batch_width = 15
    service_config.n_trials = 200
    start_experiment(robot, agents, pd, service_config, n_iter, tags=tags, keep_record=False)


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
    call_method("collective-panda-prime.local", 12002, "set_grasped_object", {"object": "key_garmi"})
    pd = insert_key("garmi")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 5
    service_config.n_gen = 10
    knowledge = None
    tags = ["pinakothek"]
    if use_prior is True:
        knowledge = {
            "mode": "specific",
            "kb_location": "collective-control-001.local",
            "kb_db": "results_tl_base",
            "kb_task_type": "insert_object",
            "kb_tags": ["transfer_learning", "key_old"]
        }
        tags = ["pinakothek", "from_cylinder_10"]
    start_experiment("collective-panda-prime", ["collective-panda-prime"], pd, service_config, 1, tags=tags, knowledge=knowledge)


def collective_learning_raw():
    call_method("collective-panda-001.local", 12002, "set_grasped_object", {"object": "generic_insertable"})
    #call_method("collective-panda-002.local", 12002, "set_grasped_object", {"object": "generic_insertable"})
    call_method("collective-panda-007.local", 12002, "set_grasped_object", {"object": "generic_insertable"})
    call_method("collective-panda-008.local", 12002, "set_grasped_object", {"object": "generic_insertable"})
    #call_method("collective-panda-009.local", 12002, "set_grasped_object", {"object": "generic_insertable"})
    agents = ["collective-panda-001", "collective-panda-007", "collective-panda-008"]

    pd = insert_generic()
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tags = ["collective_learning_multi_agent"]
    start_experiment("collective-panda-001.local", agents, pd, service_config, 10, tags=tags, knowledge=knowledge)


def collective_learning_benchmark():
    agents = ["collective-panda-007", "collective-panda-008",
              "collective-panda-009", "collective-panda-001", "collective-panda-002"]

    pd = mios_ml_benchmark(0)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    tag = "collective_learning_benchmark_multi"
    delete_local_results(agents, "ml_results", pd.task_type, [tag])
    tags = [tag]
    start_experiment(agents[0], agents, pd, service_config, 10, tags=tags, knowledge=knowledge)


def collective_learning_benchmark_2():
    agents = ["collective-panda-002.local", "collective-panda-008.local",
              "collective-panda-009.local"]

    service_config = CMAESConfiguration()
    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    #service_config.n_ind = 10
    #service_config.n_gen = 10
    service_config.n_trials = 300
    service_config.batch_width = 15
    service_config.n_immigrant = 10
    tag = "collective_learning_benchmark_share_t"
    knowledge = {"mode": "none", "kb_location": agents[0], "kb_tags": [tag]}
    threads = []
    pd = mios_ml_benchmark(0)
    delete_local_results(agents, "ml_results", pd.task_type, [tag])
    s = ServerProxy("http://" + agents[0] + ":8001", allow_none=True)
    for i in range(5):
        s.clear_memory()
        for a in agents:
            pd = mios_ml_benchmark(i * 0.1)
            pd.cost_function.geometry_factor = i * 0.1
            tags = [tag, a]
            threads.append(Thread(target=start_single_experiment, args=(a, [a], pd, service_config, i, tags, knowledge, False,)))
            threads[-1].start()

        for t in threads:
            t.join()

    for a in agents:
        if a == agents[0]:
            continue
        backup_results(a, agents[0], pd.task_type, [tag], "ml_results")


def collective_learning_experiment_2():
    agents = ["collective-panda-007", "collective-panda-008",
              "collective-panda-001"]

    call_method("collective-panda-001", 12002, "set_grasped_object", {"object": "generic_insertable"})
    #call_method("collective-panda-002", 12002, "set_grasped_object", {"object": "generic_insertable"})
    call_method("collective-panda-007", 12002, "set_grasped_object", {"object": "generic_insertable"})
    call_method("collective-panda-008", 12002, "set_grasped_object", {"object": "generic_insertable"})
    #call_method("collective-panda-009", 12002, "set_grasped_object", {"object": "generic_insertable"})

    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 13
    service_config.n_gen = 10
    tag = "collective_learning_experiment_multi"
    knowledge = None
    pd = insert_generic()
    delete_local_results(agents, "ml_results", pd.task_type, [tag])
    tags = [tag]
    start_experiment(agents[0], agents, pd, service_config, 10, tags=tags, knowledge=knowledge)


def tax_learn_move(robot: str, agents: list, n_iter: int = 1):
    pd = move("iros_loc_2", "iros_loc_1", 5)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 9
    service_config.n_gen = 20
    tags = ["iros2021", "move"]
    start_experiment(robot, agents, pd, service_config, n_iter, tags=tags, keep_record=False)


def tax_learn_turn(robot: str, agents: list, n_iter: int = 1):
    call_method(robot, 12002, "set_grasped_object", {"object": "iros_key"})
    pd = turn("iros_key", "iros_turn_goal", "iros_lock")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 8
    service_config.n_gen = 20
    tags = ["iros2021", "turn"]
    start_experiment(robot, agents, pd, service_config, n_iter, tags=tags, keep_record=False)


def tax_learn_insertion(robot: str, agents: list, n_iter: int = 1):
    call_method(robot, 12002, "set_grasped_object", {"object": "iros_key"})
    pd = tax_insertion("iros_key", "iros_lock", "iros_lock_approach")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 13
    service_config.n_gen = 20
    tags = ["iros2021", "insertion"]
    start_experiment(robot, agents, pd, service_config, n_iter, tags=tags, keep_record=False)


def generic_insertion(robot: str, agents: list, n_iter: int = 1):
    call_method(robot, 12002, "set_grasped_object", {"object": "generic_insertable"})
    pd = insert_generic()
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 13
    service_config.n_gen = 20
    tags = ["generic_insertion"]
    start_experiment(robot, agents, pd, service_config, n_iter, tags=tags, keep_record=False)


def tax_learn_extraction(robot: str, agents: list, n_iter: int = 1):
    call_method(robot, 12002, "set_grasped_object", {"object": "key_pad"})
    pd = extraction("key_pad", "lock_pad", "lock_pad_above")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 13
    service_config.n_gen = 20
    tags = ["iros2021", "extraction"]
    start_experiment(robot, agents, pd, service_config, n_iter, tags=tags, keep_record=False)


def tax_learn_press_button(robot: str, agents: list, n_iter: int = 1):
    pd = press_button("iros_button_approach", "iros_button", "iros_button_approach")
    #s = ServerProxy("http://localhost:8000", allow_none=True)
    #s.subscribe_to_event("button_press", robot, "12000")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 9
    service_config.n_gen = 20
    tags = ["iros2021", "press_button"]
    start_experiment(robot, agents, pd, service_config, n_iter, tags=tags, keep_record=False)


def tax_learn_place(robot: str, agents: list, n_iter: int = 1):
    call_method(robot, 12002, "set_grasped_object", {"object": "iros_key"})
    pd = place("iros_key_place_approach", "iros_key", "iros_key_place_approach", "iros_key_storage")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 9
    service_config.n_gen = 20
    tags = ["iros2021", "place"]
    start_experiment(robot, agents, pd, service_config, n_iter, tags=tags, keep_record=False)


def tax_learn_grab(robot: str, agents: list, n_iter: int = 1):
    pd = grab("iros_key_place_approach", "iros_key", "iros_key_place_approach", "iros_key_storage")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 9
    service_config.n_gen = 20
    tags = ["iros2021", "grab"]
    start_experiment(robot, agents, pd, service_config, n_iter, tags=tags, keep_record=False)


from definitions.taxonomy_templates import insertion


def taxonomy_learning(robot: str):
    call_method(robot, 12002, "set_grasped_object", {"object": "cylinder_30"})
    pd = insertion("cylinder_30", "cylinder_30_hole", "cylinder_30_approach")
    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.n_trials = 100
    service_config.batch_width = 10
    tags = ["taxonomy", "insertion"]
    start_experiment(robot, [robot], pd, service_config, 1, tags=tags, keep_record=False)
