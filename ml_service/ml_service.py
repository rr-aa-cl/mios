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
    problem_def = rastrigin()
    problem_def.tags = ["rastrigin_8", "collective_learning_benchmark_001"]
    interface = Interface()

    # call_method(agent, 12002, "set_grasped_object", {"object": "key_abus_e30"})
    config = get_service_configuration()
    config.n_gen = 100

    uuid = interface.start_service(problem_def, config, agents, {"mode": "global", "kb_location": "collective-panda-002.local"})
    input("Press enter to stop service.")
    interface.stop_service()


def test_with_rpc_server():
    i = Interface()
    i.start_rpc_server(8000)


def test_with_rpc_client(agent: str = "localhost"):
    agents = []
    agents.append(agent)
    problem_def = rastrigin()

    print(problem_def.to_dict())

    s = ServerProxy("http://" + agent + ":8000", allow_none=True)
    s.start_service(problem_def.to_dict(), CMAESConfiguration().to_dict(), agents, None)


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
    k = KnowledgeManager(host = "collective-panda-001.local")
    # k.process_knowledge({"meta.tags":["test_sequence_1","test_sequence_2","test_sequence_3"]},"ml_results","benchmark_rastrigin","local_knowledge","benchmark_rastrigin",["test_knowledge","some_tag"])

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
        "kb_location": "http://localhost:8001/"
    }

    uuid = interface.start_service(problem_def, get_service_configuration(), agents, knowledge_info)
    input("Press enter to stop service.")
    interface.stop_service()


def test_plotting(tags):
    hosts = [
        "collective-panda-001.local"]  # ,"collective-panda-002.local","collective-panda-007.local","collective-panda-008.local","collective-panda-009.local"]
    filter = {"meta.tags": tags}
    knowledge_mode = "global"
    # task_type = "insert_object"
    task_type = "benchmark_rastrigin"

    p = DataProcessor()
    plot = Plotter()
    results = []
    for host in hosts:
        results.extend(get_multiple_experiment_data(host, task_type, knowledge_mode, filter=filter))

    results = p.sort_over_time(results)  # not really needed results are stored in order
    # all_times = p.get_cumulative_time(results)
    # plot.plot_learning_over_task(all_times, "global")
    agent_results = p.get_agent_results(results)  # seperate results for every agent
    for agent, agent_results in agent_results.items():
        agent_times_cum = p.get_cumulative_time(agent_results)
        plot.plot_learning_over_task(agent_times_cum, agent)


from knowledge_processor.kg_linear_regression import KGLinearRegressor
from knowledge_processor.kg_random_forest import KGRandomForest
from knowledge_processor.kg_k_neighbors import KGKNeighbors
from knowledge_processor.kg_mlp import KGMLP


def test_generalizer():
    task_name = "rastrigin_0"
    task_identity = {
        "tags": ["collective_learning_benchmark_001", task_name],
        "task_type": "benchmark_rastrigin",
        "optimum_weights": [0, 0.3, 0.7, 0, 0]
    }

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
