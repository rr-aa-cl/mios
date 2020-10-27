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
from definitions import *
from xmlrpc.client import ServerProxy
import xmlrpc
from task_scheduler.creation_pipeline import CreationPipeline
from definitions import *
from task_scheduler.task_scheduler import TaskScheduler
from task_scheduler.creation_pipeline import CreationPipeline
from mongodb_client.mongodb_client import MongoDBClient

from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor
from plotting.plotter import Plotter

logger = logging.getLogger("ml_service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
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
    problem_def = rastrigin()
    problem_def.tags = ["rastrigin_8", "collective_learning_benchmark_001"]

    result_names = ["collective_learning_benchmark_screen_001", "collective_learning_benchmark_screen_002",
                    "collective_learning_benchmark_screen_003", "collective_learning_benchmark_screen_004",
                    "collective_learning_benchmark_screen_005"]
    grids = []
    for i in range(len(result_names)):
        results = get_multiple_experiment_data("collective-panda-002.local", "benchmark_rastrigin", "global",
                                               {"meta.tags": {"$all": [result_names[i]]}})
        processor = DataProcessor()
        grids.append(processor.get_optima_by_task_identity(results, 0.01))
        problem_def.cost_function.cost_grid_weights = grids[i][0, :-1]
        problem_def.cost_function.cost_grid_val = grids[i][0, -1]
        problem_def.cost_function.cost_grid_weights = problem_def.cost_function.cost_grid_weights.reshape(1, -1)
        problem_def.cost_function.cost_grid_val = problem_def.cost_function.cost_grid_val.reshape(1, -1)
        for j in range(1, grids[i].shape[0]):
            problem_def.cost_function.add_to_cost_grid(grids[i][j, 0], grids[i][j, 1:-1], grids[i][j, -1])

        ind = np.lexsort((grids[i][:, 5], grids[i][:, 4], grids[i][:, 3], grids[i][:, 2], grids[i][:, 1], grids[i][:, 0]))
        grids[i] = grids[i][ind]
        print(grids[i])

    for i in range(grids[0].shape[0]):
        tmp = np.empty((len(result_names)))
        for j in range(len(tmp)):
            tmp[j] = grids[j][i, -1]

        print("Costs at " + str(grids[0][i]) + ": " + str(tmp))

    task_identity = np.append(np.array([problem_def.cost_function.geometry_factor]), problem_def.cost_function.optimum_weights)
    for i in range(problem_def.cost_function.cost_grid_weights.shape[0]):
        if np.allclose(problem_def.cost_function.cost_grid_weights[i], task_identity):
            print("Expected optimum is: " + str(problem_def.cost_function.cost_grid_val[i]))

    return
    interface = Interface()

    # call_method(agent, 12002, "set_grasped_object", {"object": "key_abus_e30"})
    config = get_service_configuration()
    config.n_gen = 100
    config.n_ind = 10
    config.exploration_mode = True

    uuid = interface.start_service(problem_def, config, agents, None)
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

            k.process_knowledge(task_identity, "global_ml_results", "global_knowledge")
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
        prediction = manager.predict_knowledge(task_identity, "global_knowledge", regr)
        print("error: " + str(prediction["meta"]["prediction_error"]))


def test_cost_function():
    results = get_multiple_experiment_data("collective-panda-002.local", "benchmark_rastrigin", "global",
                                           {"meta.tags": {"$all": ["collective_learning_benchmark_screen_001"]}})
    processor = DataProcessor()
    print(processor.get_optima_by_task_identity(results))
