from utils.experiment_wizard import start_experiment
from definitions.insertion_definitions import insert_cylinder
from definitions.insertion_definitions import insert_key
from definitions.benchmark_definitions import mios_ml_benchmark
from services.cmaes import CMAESConfiguration
from utils.udp_client import call_method


def simple_benchmark():
    pd = mios_ml_benchmark()
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-007.local", pd, service_config, 3)


def transfer_learning_10(from_host: str = None, from_db: str = None, task: str = None, from_tag: str = None):
    call_method("collective-panda-007.local", 12002, "set_grasped_object", {"object": "cylinder_10"})
    pd = insert_cylinder(10)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    knowledge = None
    if from_host is not None:
        knowledge = {
            "mode": "specific",
            "kb_location": from_host,
            "kb_db": from_db,
            "kb_task_type": task,
            "kb_tags": ["transfer_learning", from_tag]
        }
    start_experiment("collective-panda-007", pd, service_config, 10, tags=["transfer_learning", "from_" + from_tag], knowledge=knowledge)


def transfer_learning_20():
    call_method("collective-panda-007.local", 12002, "set_grasped_object", {"object": "cylinder_20"})
    pd = insert_cylinder(20)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-007", pd, service_config, 10, tags=["transfer_learning"])


def transfer_learning_30():
    call_method("collective-panda-008.local", 12002, "set_grasped_object", {"object": "cylinder_30"})
    pd = insert_cylinder(30)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-008", pd, service_config, 10, tags=["transfer_learning"])


def transfer_learning_40():
    call_method("collective-panda-001.local", 12002, "set_grasped_object", {"object": "cylinder_40"})
    pd = insert_cylinder(40)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-001", pd, service_config, 10, tags=["transfer_learning"])


def transfer_learning_50():
    call_method("collective-panda-001.local", 12002, "set_grasped_object", {"object": "cylinder_50"})
    pd = insert_cylinder(50)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-001", pd, service_config, 10, tags=["transfer_learning"])


def transfer_learning_60():
    call_method("collective-panda-008.local", 12002, "set_grasped_object", {"object": "cylinder_60"})
    pd = insert_cylinder(60)
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-008", pd, service_config, 10, tags=["transfer_learning"])


def transfer_learning_abus_e30():
    call_method("collective-panda-002.local", 12002, "set_grasped_object", {"object": "key_abus_e30"})
    pd = insert_key("abus_e30")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-002", pd, service_config, 10, tags=["transfer_learning"])


def transfer_learning_pad_lock():
    call_method("collective-panda-009.local", 12002, "set_grasped_object", {"object": "key_pad"})
    pd = insert_key("pad")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-009", pd, service_config, 10, tags=["transfer_learning"])


def transfer_learning_old_key():
    call_method("collective-panda-009.local", 12002, "set_grasped_object", {"object": "key_old"})
    pd = insert_key("old")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-009", pd, service_config, 10, tags=["transfer_learning"])


def transfer_learning_hatch_key():
    call_method("collective-panda-002.local", 12002, "set_grasped_object", {"object": "key_hatch"})
    pd = insert_key("hatch")
    service_config = CMAESConfiguration()
    service_config.exploration_mode = True
    service_config.n_ind = 10
    service_config.n_gen = 10
    start_experiment("collective-panda-002", pd, service_config, 10, tags=["transfer_learning"])
