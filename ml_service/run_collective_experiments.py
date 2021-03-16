from utils.experiment_wizard import *
from services.svm import SVMConfiguration
from utils.udp_client import call_method
from utils.database import delete_local_results
from utils.database import delete_local_knowledge
from utils.database import backup_results
from definitions.insertion_definitions import insert_generic
from definitions.benchmark_definitions import mios_ml_benchmark
from threading import Thread
from xmlrpc.client import ServerProxy
import numpy as np
from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor
from plotting.data_processor import DataError
from plotting.plotter import Plotter
import matplotlib.pyplot as plt

benchmark_factors = [0, 0.1, 0.2, 0.3, 0.4]
benchmark_learning_thresholds = [0.01, 0.01, 0.01, 0.01]
experiment_factors = [0, 0.1, 0.2, 0.3]
experiment_learning_thresholds = [0.225, 0.21, 0.172, 0.156]
database = "collective-control-001.local"
agents_benchmark = ["collective-panda-001", "collective-panda-002", "collective-panda-003",
          "collective-panda-008", "collective-panda-009"]
agents_experiment = ["collective-panda-001", "collective-panda-007",
          "collective-panda-008", "collective-panda-009"]
base_batch_size_benchmark = 5
n_trials_benchmark = 200
base_batch_size_experiment = 15
n_trials_experiment = 180


def benchmark_single(agent: str,  unique_tag: str, n_iter: int = 1):
    pd = mios_ml_benchmark(0)
    delete_local_results([agent], "ml_results", pd.task_type, ["collective_benchmark_single"])
    for f in benchmark_factors:
        tags = ["collective_benchmark_single", "f_" + str(f), unique_tag]
        pd = mios_ml_benchmark(f)
        service_config = SVMConfiguration()
        service_config.exploration_mode = True
        service_config.batch_width = base_batch_size_benchmark
        service_config.n_trials = n_trials_benchmark
        start_experiment(agent, [agent], pd, service_config, n_iter, tags=tags, keep_record=False)

    backup_results(agent, database, pd.task_type, ["collective_benchmark_single"], "collective_data")


def benchmark_collective(agents: list, unique_tag: str, n_iter: int = 1):
    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.n_trials = n_trials_benchmark
    service_config.batch_width = base_batch_size_benchmark * len(agents)
    service_config.n_immigrant = service_config.batch_width - base_batch_size_benchmark
    tag = "collective_benchmark_shared"
    knowledge = {"mode": "none", "kb_location": agents[0], "kb_tags": [tag]}
    threads = []
    pd = mios_ml_benchmark(0)
    delete_local_results(agents, "ml_results", pd.task_type, [tag])
    delete_local_results([database], "collective_data", pd.task_type, [tag])
    s = ServerProxy("http://" + agents[0] + ":8001", allow_none=True)
    for i in range(n_iter):
        s.clear_memory()
        j = 0
        for a in agents:
            pd = mios_ml_benchmark(benchmark_factors[j])
            pd.cost_function.geometry_factor = benchmark_factors[j]
            tags = [tag, a, unique_tag, "f_" + str(benchmark_factors[j])]
            threads.append(
                Thread(target=start_single_experiment, args=(a, [a], pd, service_config, i, tags, knowledge, False,)))
            threads[-1].start()
            j += 1

        for t in threads:
            t.join()

    for a in agents:
        backup_results(a, database, pd.task_type, [tag], "collective_data")


def experiment_single(agent: str,  unique_tag: str, factor: float, n_iter: int = 1):
    call_method(agent, 12002, "set_grasped_object", {"object": "generic_insertable"})
    pd = insert_generic()
    delete_local_results([agent], "ml_results", pd.task_type, ["collective_experiment_single", unique_tag])
    tags = ["collective_experiment_single", "f_" + str(factor), unique_tag]
    pd = insert_generic()
    pd.cost_function.geometry_factor = factor
    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.batch_width = base_batch_size_experiment
    service_config.n_trials = n_trials_experiment
    start_experiment(agent, [agent], pd, service_config, n_iter, tags=tags, keep_record=False)

    backup_results(agent, database, pd.task_type, ["collective_experiment_single", unique_tag], "collective_data")


def experiment_collective(agents: list, unique_tag: str, n_iter: int = 1):

    for a in agents:
        call_method(a, 12002, "set_grasped_object", {"object": "generic_insertable"})

    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.n_trials = n_trials_experiment
    service_config.batch_width = base_batch_size_experiment * len(agents)
    service_config.n_immigrant = service_config.batch_width - base_batch_size_experiment
    tag = "collective_experiment_shared"
    knowledge = {"mode": "none", "kb_location": agents[0], "kb_tags": [tag]}
    threads = []
    pd = insert_generic()
    delete_local_results(agents, "ml_results", pd.task_type, [tag])
    delete_local_results([database], "collective_data", pd.task_type, [tag, unique_tag])
    s = ServerProxy("http://" + agents[0] + ":8001", allow_none=True)
    for i in range(n_iter):
        s.clear_memory()
        j = 0
        for a in agents:
            pd = insert_generic()
            pd.cost_function.geometry_factor = experiment_factors[j]
            tags = [tag, a, unique_tag, "f_" + str(experiment_factors[j])]
            threads.append(
                Thread(target=start_single_experiment, args=(a, [a], pd, service_config, i, tags, knowledge, False,)))
            threads[-1].start()
            j += 1

        for t in threads:
            t.join()

    for a in agents:
        backup_results(a, database, pd.task_type, [tag, unique_tag], "collective_data")


def plot_data_comparison(unique_tag_single: str, unique_tag_shared: str, benchmark: bool = True):
    if benchmark is True:
        marker = "collective_benchmark"
        skill = "benchmark_rastrigin"
        factors = benchmark_factors
        learning_thresholds = benchmark_learning_thresholds
    else:
        marker = "collective_experiment"
        skill = "insert_object"
        factors = experiment_factors
        learning_thresholds = experiment_learning_thresholds

    fig, axes = plt.subplots(2, len(factors), sharey=True, gridspec_kw={'hspace': 0.2, 'wspace': 0})

    p = DataProcessor()

    knowledge_time_single = [0]
    knowledge_time_shared = [0]
    knowledge_time_parallel = [0]

    for i in range(len(factors)):
        tags_single = [marker + "_single", unique_tag_single, "f_" + str(factors[i])]
        try:
            results_single = get_multiple_experiment_data(database, skill,
                                                   results_db="collective_data",
                                                   filter={"meta.tags": {"$all": tags_single}})
        except DataNotFoundError:
            print("No data found for tags: " + str(tags_single))
            continue
        cost_trial_single = p.get_average_cost(results_single, True)
        cost_time_single, confidence = p.get_average_cost_over_time(results_single, decreasing=True)

        knowledge_time_single.append(get_learning_duration(cost_time_single, learning_thresholds[i])+knowledge_time_single[-1])
        knowledge_time_parallel.append(get_learning_duration(cost_time_single, learning_thresholds[i]))

        axes[0, i].plot(cost_trial_single * 5)
        axes[1, i].plot(cost_time_single * 5)
        axes[0, i].set_xlabel("Trial [1]")
        axes[1, i].set_xlabel("Time [s]")
        axes[0, i].set_title("Task" + str(factors[i]))

        tags_shared = [marker + "_shared", unique_tag_shared, "f_" + str(factors[i])]
        try:
            results_shared = get_multiple_experiment_data(database, skill,
                                                          results_db="collective_data",
                                                          filter={"meta.tags": {"$all": tags_shared}})
        except DataNotFoundError:
            print("No data found for tags: " + str(tags_shared))
            continue
        cost_trial_shared = p.get_average_cost(results_shared, True)
        cost_time_shared, confidence = p.get_average_cost_over_time(results_shared, min_length=len(cost_time_single), decreasing=True)

        knowledge_time_shared.append(get_learning_duration(cost_time_shared, learning_thresholds[i]))

        axes[0, i].plot(cost_trial_shared * 5)
        axes[1, i].plot(cost_time_shared * 5)
        axes[0, i].set_xlabel("Trial [1]")
        axes[1, i].set_xlabel("Time [s]")
        axes[0, i].set_title("Task" + str(factors[i]))

        axes[0, i].set_ylim(0, 5)
        axes[1, i].set_ylim(0, 5)
        plt.legend(("Single", "Shared"))

        #axes[0, i].plot(get_difference_function(cost_trial_single, cost_trial_shared))
        #axes[1, i].plot(get_difference_function(cost_time_single, cost_time_shared))

        if i == 0:
            axes[0, i].set_ylabel("Cost [s]")
            axes[1, i].set_ylabel("Cost [s]")

    knowledge_time_shared.sort()
    knowledge_time_parallel.sort()

    fig_knowledge, axes_knowledge = plt.subplots()
    axes_knowledge.plot(knowledge_time_single, np.linspace(0, len(knowledge_time_single) - 1, len(knowledge_time_single)))
    axes_knowledge.plot(knowledge_time_parallel, np.linspace(0, len(knowledge_time_parallel) - 1, len(knowledge_time_parallel)))
    axes_knowledge.plot(knowledge_time_shared, np.linspace(0, len(knowledge_time_shared) - 1, len(knowledge_time_shared)))

    axes_knowledge.legend(("Single", "Parallel", "Shared"))

    plt.show()


def get_learning_duration(cost: np.ndarray, threshold: float):
    return np.where(cost <= threshold)[0][0]


def get_difference_function(cost1: np.ndarray, cost2: np.ndarray):
    if len(cost1) > len(cost2):
        cost2 = np.append(cost2, np.asarray([cost2[-1]] * (len(cost1) - len(cost2))))

    if len(cost2) > len(cost1):
        print([cost1[-1] * (len(cost2) - len(cost1))])
        cost1 = np.append(cost1, [cost1[-1]] * (len(cost2) - len(cost1)))

    diff = []
    for i in range(len(cost1)):
        diff.append(abs(cost1[i]-cost2[i]))

    return diff


def command_collective(cmd: str, external_network: bool = True):
    threads = []
    for a in agents_experiment:
        agent = a
        if external_network is True:
            agent = a + ".local"
        threads.append(Thread(target=call_method, args=(agent, 12002, cmd,)))
        threads[-1].start()

    for t in threads:
        t.join()


def teach_generic_insertable(agent: str):
    call_method(agent, 12002, "set_grasped_object", {"object": "generic_insertable"})
    input("Press Enter to teach the approach pose.")
    call_method(agent, 12002, "teach_object", {"object": "generic_approach"})
    input("Press Enter to teach the container pose.")
    call_method(agent, 12002, "teach_object", {"object": "generic_container"})