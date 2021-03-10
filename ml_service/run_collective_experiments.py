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
database = "collective-control-001.local"
agents = ["collective-panda-001", "collective-panda-002", "collective-panda-003",
          "collective-panda-008", "collective-panda-009"]
base_batch_size = 5
n_trials = 200


def benchmark_single(agent: str,  unique_tag: str, n_iter: int = 1):
    pd = mios_ml_benchmark(0)
    delete_local_results([agent], "ml_results", pd.task_type, ["collective_benchmark_single"])
    for f in benchmark_factors:
        tags = ["collective_benchmark_single", "f_" + str(f), unique_tag]
        pd = mios_ml_benchmark(f)
        service_config = SVMConfiguration()
        service_config.exploration_mode = True
        service_config.batch_width = base_batch_size
        service_config.n_trials = n_trials
        start_experiment(agent, [agent], pd, service_config, n_iter, tags=tags, keep_record=False)

    backup_results(agent, database, pd.task_type, ["collective_benchmark_single"], "collective_data")


def benchmark_collective(agents: list, unique_tag: str, n_iter: int = 1):
    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.n_trials = n_trials
    service_config.batch_width = base_batch_size * len(agents)
    service_config.n_immigrant = service_config.batch_width - base_batch_size
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

        for t in threads:
            t.join()

        j += 1

    for a in agents:
        backup_results(a, database, pd.task_type, [tag], "collective_data")


def plot_data_comparison(unique_tag: str):
    fig, axes = plt.subplots(2, len(benchmark_factors), sharey=True, gridspec_kw={'hspace': 0.2, 'wspace': 0})

    p = DataProcessor()

    for i in range(len(benchmark_factors)):
        # tags_single = ["collective_benchmark_single", unique_tag, "f_" + str(benchmark_factors[i])]
        # results_single = get_multiple_experiment_data(database, "benchmark_rastrigin",
        #                                        results_db="collective_data",
        #                                        filter={"meta.tags": {"$all": tags_single}})
        # cost_trial = p.get_average_cost(results_single, True)
        # cost_time = p.get_average_cost_over_time(results_single)
        #
        # axes[0, i].plot(cost_trial)
        # axes[1, i].plot(cost_time)
        # axes[0, i].set_xlabel("Trial [1]")
        # axes[1, i].set_xlabel("Time [s]")
        # axes[0, i].set_title("Task" + str(benchmark_factors[i]))

        tags_shared = ["collective_benchmark_shared", unique_tag, "f_" + str(benchmark_factors[i])]
        try:
            results_shared = get_multiple_experiment_data(database, "benchmark_rastrigin",
                                                          results_db="collective_data",
                                                          filter={"meta.tags": {"$all": tags_shared}})
        except DataNotFoundError:
            print("No data found for tags: " + str(tags_shared))
        cost_trial = p.get_average_cost(results_shared, True)
        cost_time = p.get_average_cost_over_time(results_shared)

        axes[0, i].plot(cost_trial)
        axes[1, i].plot(cost_time)
        axes[0, i].set_xlabel("Trial [1]")
        axes[1, i].set_xlabel("Time [s]")
        axes[0, i].set_title("Task" + str(benchmark_factors[i]))

        if i == 0:
            axes[0, i].set_ylabel("Cost [s]")
            axes[1, i].set_ylabel("Cost [s]")

    plt.show()