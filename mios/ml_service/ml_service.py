import logging
import time
import sys
import numpy as np
from knowledge_processor.knowledge_manager import KnowledgeManager
from services.basinhopping import BasinhoppingService
from services.cmaes import *
from interface.interface import Interface
from services.generic_optimizer import *
from utils.udp_client import call_method
from xmlrpc.client import ServerProxy
import xmlrpc
from task_scheduler.task_scheduler import TaskScheduler
from definitions.insertion_definitions import insert_cylinder
from definitions.benchmark_definitions import mios_ml_benchmark

from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor

logger = logging.getLogger("ml_service")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def get_service_configuration():
    configuration = CMAESConfiguration()
    configuration.n_ind = 5
    configuration.n_gen = 10
    return configuration


def test_mios(agent: str = "localhost"):
    agents = set()
    agents.add(agent)

    pd = rastrigin()

    payload = {
        "problem_definition": pd.to_dict(),
        "service_configuration": get_service_configuration().to_dict(),
        "agents": list(agents)
    }

    response = call_method(agent, 12002, "learn_task", payload)
    print(response)


def test_interface(agent: str = "localhost"):
    agents = set()
    agents.add(agent)
    problem_def = mios_ml_benchmark(0)
    problem_def.cost_function.optimum_weights[1] = 0.8
    problem_def.cost_function.optimum_weights[2] = 0.2

    interface = Interface()

    # call_method(agent, 12002, "set_grasped_object", {"object": "key_abus_e30"})
    config = get_service_configuration()
    config.n_gen = 2
    config.n_ind = 5
    config.exploration_mode = True

    knowledge = {
        "mode": "global",
        "type": "predicted",
        "kb_location": "localhost",
        "kb_db": "ml_results",
        "kb_task_type": "benchmark_rastrigin"
    }
    uuid = interface.start_service(problem_def, config, agents, knowledge)
    input("Press enter to stop service.")
    interface.stop_service()


def test_with_rpc_server():
    i = Interface()
    i.start_rpc_server(8000)


def insert_key_abus():
    pd = insert_cylinder_30()
    pd.default_context["parameters"]["insertable"] = "key_abus_e30"
    pd.default_context["parameters"]["insert_into"] = "lock_abus_e30"
    pd.default_context["parameters"]["insert_approach"] = "lock_abus_e30_above"
    pd.default_context["skills"]["insertion"]["skill"]["ROI_x"] = [-0.01, 0.01, -0.01, 0.01, -1, 1]
    pd.reset_instructions[0]["parameters"]["parameters"]["extractable"] = "key_abus_e30"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_from"] = "lock_abus_e30"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_to"] = "lock_abus_e30_above"
    pd.tags = ["key_abus_e30"]
    return pd


def test_with_rpc_client(agent: str = "localhost"):
    agents = []
    agents.append(agent)
    problem_def = insert_key_abus()
    problem_def.tags = ["key_recording"]

    # call_method(agent, 12002, "set_grasped_object", {"object": "key_abus_e30"})
    config = get_service_configuration()
    config.n_gen = 100
    config.n_ind = 10
    config.exploration_mode = True

    s = ServerProxy("http://" + agent + ":8000", allow_none=True)
    s.start_service(problem_def.to_dict(), config.to_dict(), agents, None)


def test_standalone(agent: str = "localhost"):
    agents = set()
    agents.add(agent)
    learner = GenericOptimizerService()
    learner.initialize(rastrigin(), get_service_configuration(), agents)
    learner.learn_task()


def test_task_scheduler():
    t = TaskScheduler()
    c = CreationPipeline()
    c.create_tasks_from_template(rastrigin(), get_service_configuration(), 10, "http://localhost:8000", ["localhost"],
                                 "none")
    for task in c.tasks:
        t.add_task(task)

    t.solve_tasks()


def test_server_connection(host):
    s = ServerProxy(host)
    print(s.is_busy())


def test_knowledge_use(knowledge_mode="global"):
    import time
    # create knowledge from old task:
    k = KnowledgeManager(host = "collective-panda-002.local")
    for i in range(5):
        for j in range(200):
            task_identity = {
                "tags": ["collective_learning_benchmark_screen_006"],
                "task_type": "benchmark_rastrigin",
                "optimum_weights": [0, j / 200.0, 1 - (j / 200.0), 0, 0],
                "geometry_factor": i + 1
            }

            k.process_knowledge_by_identity(task_identity, "global_ml_results", "global_knowledge")
            print(j + i * 200)

    return

    # start global database:
    interface = Interface()
    time.sleep(1)
    # interface.stop_global_database()

    time.sleep(1)

    agents = set()
    agent = 'localhost'
    agents.add(agent)
    problem_def = rastrigin()
    problem_def.tags = ["collective_learning_benchmark_003", "rastrigin_8"]

    knowledge_info = {
        "mode": knowledge_mode,
        "kb_location": "http://localhost:8001/",
        "type": "similar"
    }

    uuid = interface.start_service(problem_def, get_service_configuration(), agents, knowledge_info)
    input("Press enter to stop service.")
    interface.stop_service()


from knowledge_processor.kg_linear_regression import KGLinearRegressor
from knowledge_processor.kg_random_forest import KGRandomForest
from knowledge_processor.kg_k_neighbors import KGKNeighbors
from knowledge_processor.kg_mlp import KGMLP


def test_generalizer():
    task_name = "rastrigin_1"
    task_identity = {
        "tags": ["collective_learning_benchmark_screen_006"],
        "task_type": "benchmark_rastrigin",
        "geometry_factor": 1,
        "optimum_weights": [0, 0.3, 0.7, 0, 0]
    }

    # data = get_experiment_data("collective-panda-002.local", "benchmark_rastrigin", "global", task_identity)

    manager = KnowledgeManager(host="collective-panda-002.local")

    regressors = {
        "lr": KGLinearRegressor(),
        "rf": KGRandomForest(),
        "kn": KGKNeighbors(),
        "mlp": KGMLP()
    }

    for name, regr in regressors.items():
        print("--------------------------------------")
        print("Regressor: " + name)
        prediction = manager.get_predicted_knowledge(task_identity, "global_knowledge", regr)
        print("error: " + str(prediction["meta"]["prediction_error"]))


def test_knowledge():
    km = KnowledgeManager("collective-panda-001.local")
    client = MongoDBClient("collective-panda-001.local")
    knowledge = km.get_knowledge_by_filter(client, "ml_results", "insert_object", {"meta.tags": {"$all": ["transfer_learning", "cylinder_50", "n1"]}})
    print(knowledge)


def test_trial_pushing(host: str):
    s = ServerProxy("http://" + host + ":8001", allow_none=True)

    agents = ["a1", "a2", "a3"]
    for a in agents:
        for i in range(5):
            s.push_trial_2(random.sample(range(-30, 30), 6), random.random(), 0)

    print(s.request_online_evaluation([5,2,5,7,9,10], 0))
