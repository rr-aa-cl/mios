from utils.experiment_wizard import *
from services.svm import SVMConfiguration
from services.cmaes import CMAESConfiguration
from utils.ws_client import call_method
from utils.database import delete_local_results
from utils.database import delete_local_knowledge
from utils.database import backup_results
from definitions.benchmark_definitions import mios_ml_benchmark
from definitions.benchmark_definitions import mios_complex_ml_benchmark
from threading import Thread
from xmlrpc.client import ServerProxy
import numpy as np
from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor
from plotting.data_processor import DataError
from plotting.plotter import Plotter
import matplotlib.pyplot as plt
import scipy.stats
from definitions.templates import *
from definitions.cost_functions import *
from definitions.service_configs import *

benchmark_factors = [0, 0.1, 0.2, 0.3, 0.4]
benchmark_learning_thresholds = [0.01, 0.01, 0.01, 0.01]
experiment_factors = [0, 0.1, 0.2, 0.3, 0.4]
experiment_learning_thresholds = [0.7/5, 0.5/5, 0.6/5, 0.7/5, 0.6/5]
#experiment_learning_thresholds = [1, 1, 1, 1]
database = "collective-control-001.local"
agents_benchmark = ["collective-panda-001", "collective-panda-003"]
agents_experiment = ["collective-panda-001", "collective-panda-002", "collective-panda-007","collective-panda-009"]
var_exp_agents = ["collective-panda-001", "collective-panda-002", "collective-panda-004","collective-panda-007",
                  "collective-panda-008"]

task_map = {
    "collective-panda-001": "cylinder_40",
    "collective-panda-002": "key_abus_e30",
    "collective-panda-003": "plug_eth",
    "collective-panda-007": "cylinder_20",
    "collective-panda-008": "cylinder_30",
    "collective-panda-009": "key_old",
}

base_batch_size_benchmark = 15
n_trials_benchmark = 300
base_batch_size_experiment = 15
n_trials_experiment = 600


def insert_generic() -> ProblemDefinition:
    insertable = "generic_insertable"
    insert_into = "generic_container"
    approach = "generic_container_approach"
    pd = insertion(insertable, insert_into, approach)
    pd.domain.limits["p0_offset_x"] = (-0.002, 0.002)
    pd.domain.limits["p0_offset_y"] = (-0.002, 0.002)
    return pd


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


def experiment_single(agent: str,  unique_tag: str, n_iter: int = 1):
    call_method(agent, 12000, "set_grasped_object", {"object": "generic_insertable"})
    pd = insertion("generic_insertable", "generic_container", "generic_container_approach")
    # delete_local_results([agent], "ml_results", pd.skill_class, ["collective_experiment_single", unique_tag])
    tags = ["collective_experiment_single", "task_" + str(task_map[agent]), unique_tag]
    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.batch_width = base_batch_size_experiment
    service_config.n_trials = n_trials_experiment
    start_experiment(agent, [agent], pd, service_config, n_iter, tags=tags, keep_record=True)

    backup_results(agent, database, pd.skill_class, ["collective_experiment_single", unique_tag], "collective_data")


def experiment_collective(agents: list, unique_tag: str, n_iter: int = 1):

    for a in agents:
        call_method(a, 12000, "set_grasped_object", {"object": "generic_insertable"})

    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.n_trials = n_trials_experiment
    service_config.batch_width = base_batch_size_experiment * len(agents)
    service_config.n_immigrant = service_config.batch_width - base_batch_size_experiment
    tag = "collective_experiment_shared"
    knowledge = {"mode": "none", "kb_location": agents[0], "kb_tags": [tag]}
    threads = []
    pd = insert_generic()
    delete_local_results(agents, "ml_results", pd.skill_class, [tag])
    delete_local_results([database], "collective_data", pd.skill_class, [tag, unique_tag])
    s = ServerProxy("http://" + agents[0] + ":8001", allow_none=True)
    for i in range(n_iter):
        s.clear_memory()
        j = 0
        for a in agents:
            pd = insert_generic()
            tags = [tag, a, unique_tag, "task_" + task_map[a]]
            threads.append(
                Thread(target=start_single_experiment, args=(a, [a], pd, service_config, i, tags, knowledge, False,)))
            threads[-1].start()
            j += 1

        for t in threads:
            t.join()

    for a in agents:
        backup_results(a, database, pd.skill_class, [tag, unique_tag], "collective_data")


def plot_success():
    p = DataProcessor()
    marker = "collective_experiment"
    factors = experiment_factors
    unique_tag_single = "run_3"
    tags_single = [marker + "_single", unique_tag_single, "f_" + str(factors[0])]
    results_single = get_multiple_experiment_data(database, "insert_object",
                                                  results_db="collective_data",
                                                  filter={"meta.tags": {"$all": tags_single}})
    success, time = p.get_average_success_over_time(results_single)
    for i in range(1,len(success)):
        success[i] += success[i-1]
    plt.plot(success)
    plt.show()


def plot_data_comparison(unique_tag_single: str, unique_tag_shared: str, agents: list, benchmark: bool = True):
    if benchmark is True:
        marker = "collective_benchmark"
        skill = "benchmark_rastrigin"
        factors = benchmark_factors
        learning_thresholds = benchmark_learning_thresholds
    else:
        marker = "collective_experiment"
        skill = "insertion"
        factors = experiment_factors
        learning_thresholds = experiment_learning_thresholds

    fig, axes = plt.subplots(2, len(factors), sharey=True, gridspec_kw={'hspace': 0.2, 'wspace': 0})
    fig_asr, axes_asr = plt.subplots(2, len(factors), sharey=True, gridspec_kw={'hspace': 0.2, 'wspace': 0})
    fig_casr, axes_casr = plt.subplots(2, len(factors), gridspec_kw={'hspace': 0.2, 'wspace': 0})

    p = DataProcessor()

    knowledge_time_single = []
    knowledge_time_shared = []
    knowledge_time_parallel = []

    i = 0
    for a in agents:
        found_single = True
        found_shared = True

        tags_single = [marker + "_single", unique_tag_single, "task_" + task_map[a]]
        try:
            results_single = get_multiple_experiment_data(database, skill,
                                                   results_db="collective_data",
                                                   filter={"meta.tags": {"$all": tags_single}})

            cost_trial_single, confidence_trial = p.get_average_cost(results_single, True)
            cost_time_single, confidence_time = p.get_average_cost_over_time(results_single, decreasing=True)
            asr_trial_single, confidence_asr_trial = p.get_average_success(results_single)
            asr_time_single, confidence_asr_time = p.get_average_success_over_time(results_single)
            casr_trial_single, confidence_casr_trial = p.get_average_success(results_single)
            casr_time_single, confidence_casr_time = p.get_average_success_over_time(results_single)

            for j in range(1, len(casr_trial_single)):
                casr_trial_single[j] += casr_trial_single[j - 1]

            for j in range(1, len(casr_time_single)):
                casr_time_single[j] += casr_time_single[j - 1]

            knowledge_time_single.append(
                get_learning_time(p.get_collection_of_costs_over_time(results_single, decreasing=True),
                                  learning_thresholds[i], p))
            knowledge_time_parallel.append(
                get_learning_time(p.get_collection_of_costs_over_time(results_single, decreasing=True),
                                  learning_thresholds[i], p))
            # knowledge_time_parallel.append(get_learning_time(results_single, learning_thresholds[i], p))

            axes[0, i].plot(cost_trial_single * 5, "g")
            axes[0, i].fill_between(np.linspace(0, len(cost_trial_single), len(cost_trial_single)),
                                    cost_trial_single * 5 - confidence_trial * 5,
                                    cost_trial_single * 5 + confidence_trial * 5, alpha=0.2, color="g")
            axes[1, i].plot(cost_time_single * 5, "g")
            axes[1, i].fill_between(np.linspace(0, len(cost_time_single), len(cost_time_single)),
                                    cost_time_single * 5 - confidence_time * 5,
                                    cost_time_single * 5 + confidence_time * 5, alpha=0.2, color="g")

            axes_asr[0, i].plot(asr_trial_single, "g")
            axes_asr[1, i].plot(asr_time_single, "g")

            axes_casr[0, i].plot(casr_trial_single, "g")
            axes_casr[1, i].plot(casr_time_single, "g")

        except DataNotFoundError:
            print("No data found for tags: " + str(tags_single))
            found_single = False

        tags_shared = [marker + "_shared", unique_tag_shared, "task_" + task_map[a]]
        try:
            results_shared = get_multiple_experiment_data(database, skill,
                                                          results_db="collective_data",
                                                          filter={"meta.tags": {"$all": tags_shared}})

            cost_trial_shared, confidence_trial = p.get_average_cost(results_shared, True)
            cost_time_shared, confidence_time = p.get_average_cost_over_time(results_shared, decreasing=True)
            asr_trial_shared, confidence_asr_trial = p.get_average_success(results_shared)
            asr_time_shared, confidence_asr_time = p.get_average_success_over_time(results_shared)
            casr_trial_shared, confidence_casr_trial = p.get_average_success(results_shared)
            casr_time_shared, confidence_casr_time = p.get_average_success_over_time(results_shared)

            for j in range(1, len(casr_trial_shared)):
                casr_trial_shared[j] += casr_trial_shared[j - 1]

            for j in range(1, len(casr_time_shared)):
                casr_time_shared[j] += casr_time_shared[j - 1]

            knowledge_time_shared.append(
                get_learning_time(p.get_collection_of_costs_over_time(results_shared, decreasing=True),
                                  learning_thresholds[i], p))
            # knowledge_time_shared.append(get_learning_time(results_shared, learning_thresholds[i], p))

            axes[0, i].plot(cost_trial_shared * 5, "b")
            axes[0, i].fill_between(np.linspace(0, len(cost_trial_shared), len(cost_trial_shared)),
                                    cost_trial_shared * 5 - confidence_trial * 5,
                                    cost_trial_shared * 5 + confidence_trial * 5, alpha=0.2, color="b")
            axes[1, i].plot(cost_time_shared * 5, "b")
            axes[1, i].fill_between(np.linspace(0, len(cost_time_shared), len(cost_time_shared)),
                                    cost_time_shared * 5 - confidence_time * 5,
                                    cost_time_shared * 5 + confidence_time * 5, alpha=0.2, color="b")

            axes[0, i].set_ylim(0, 5)
            axes[1, i].set_ylim(0, 5)

            axes_asr[0, i].plot(asr_trial_shared, "b")
            axes_asr[1, i].plot(asr_time_shared, "b")

            axes_casr[0, i].plot(casr_trial_shared, "b")
            axes_casr[1, i].plot(casr_time_shared, "b")
        except DataNotFoundError:
            print("No data found for tags: " + str(tags_shared))
            found_shared = False

        if found_single is False and found_shared is False:
            continue

        if found_single is True:
            plot_trial_length = len(casr_trial_single)
            plot_time_length = len(casr_time_single)
        elif found_shared is True:
            plot_trial_length = len(casr_trial_shared)
            plot_time_length = len(casr_time_shared)

        axes_asr[0, i].set_ylim(0, 1)
        axes_asr[1, i].set_ylim(0, 1)
        axes_casr[0, i].set_xlabel("Trial [1]")
        axes_casr[1, i].set_xlabel("Time [s]")
        axes_casr[0, i].set_title("Task" + str(factors[i]))

        axes_casr[0, i].plot([0, plot_trial_length], [0, plot_trial_length], color="black", linestyle="dashed")
        axes_casr[1, i].plot([0, plot_time_length], [0, plot_time_length], color="black", linestyle="dashed")

        axes_casr[0, i].set_ylim(0, plot_trial_length)
        axes_casr[1, i].set_ylim(0, plot_time_length)

        axes_casr[0, i].set_xlim(0, plot_trial_length)
        axes_casr[1, i].set_xlim(0, plot_time_length)

        #axes[0, i].plot(get_difference_function(cost_trial_single, cost_trial_shared))
        #axes[1, i].plot(get_difference_function(cost_time_single, cost_time_shared))

        if i == 0:
            axes[0, i].set_ylabel("Cost [s]")
            axes[1, i].set_ylabel("Cost [s]")
            axes_asr[0, i].set_ylabel("Average Success Rate [1]")
            axes_asr[1, i].set_ylabel("Average Success Rate [1]")
            axes_asr[0, i].set_ylabel("Cumulative Average Success Rate [1]")
            axes_asr[1, i].set_ylabel("Cumulative Average Success Rate [1]")
        else:
            axes_casr[0, i].set_yticks([])
            axes_casr[1, i].set_yticks([])

        if i == len(factors)-1:
            axes[1, i].legend(("Single Learning", "Collective Learning"))
            axes_asr[1, i].legend(("Single Learning", "Collective Learning"))
            axes_casr[1, i].legend(("Single Learning", "Collective Learning", "Optimal Success Rate"))

        i += 1

    fig_knowledge, axes_knowledge = plt.subplots()

    knowledge_time_single_avg, knowledge_time_single_conf = get_average_and_confidence(knowledge_time_single)
    knowledge_time_parallel_avg, knowledge_time_parallel_conf = get_average_and_confidence(knowledge_time_parallel)
    knowledge_time_shared_avg, knowledge_time_shared_conf = get_average_and_confidence(knowledge_time_shared)

    for i in range(1,len(knowledge_time_single_avg)):
        knowledge_time_single_avg[i] += knowledge_time_single_avg[i-1]

    knowledge_time_single_avg = np.insert(knowledge_time_single_avg, 0, 0)
    knowledge_time_single_conf = np.insert(knowledge_time_single_conf, 0, 0)
    knowledge_time_parallel_avg = np.insert(knowledge_time_parallel_avg, 0, 0)
    knowledge_time_parallel_conf = np.insert(knowledge_time_parallel_conf, 0, 0)
    knowledge_time_shared_avg = np.insert(knowledge_time_shared_avg, 0, 0)
    knowledge_time_shared_conf = np.insert(knowledge_time_shared_conf, 0, 0)

    knowledge_units_single = np.linspace(0, len(knowledge_time_single_avg)-1, len(knowledge_time_single_avg))
    knowledge_units_parallel = np.linspace(0, len(knowledge_time_parallel_avg) - 1, len(knowledge_time_parallel_avg))
    knowledge_units_shared = np.linspace(0, len(knowledge_time_shared_avg) - 1, len(knowledge_time_shared_avg))

    axes_knowledge.fill_betweenx(knowledge_units_single,
                         knowledge_time_single_avg - knowledge_time_single_conf,
                         knowledge_time_single_avg + knowledge_time_single_conf, alpha=0.2, color="g")
    axes_knowledge.plot(knowledge_time_single_avg, knowledge_units_single, "g")

    axes_knowledge.fill_betweenx(knowledge_units_parallel,
                                knowledge_time_parallel_avg - knowledge_time_parallel_conf,
                                knowledge_time_parallel_avg + knowledge_time_parallel_conf, alpha=0.2, color="r")
    axes_knowledge.plot(knowledge_time_parallel_avg, knowledge_units_parallel, "r")

    axes_knowledge.fill_betweenx(knowledge_units_shared,
                                knowledge_time_shared_avg - knowledge_time_shared_conf,
                                knowledge_time_shared_avg + knowledge_time_shared_conf, alpha=0.2, color="b")
    axes_knowledge.plot(knowledge_time_shared_avg, knowledge_units_shared, "b")
    #axes_knowledge.plot(knowledge_time_single_avg, np.linspace(0,  len(knowledge_time_single_avg)-1, len(knowledge_time_single_avg)))
    axes_knowledge.legend(("Single Learning", "Parallel Learning", "Collective Learning"))

    plt.xlabel("Time [s]")
    plt.ylabel("Tasks Learned [1]")
    plt.title("Knowledge acquisition for four insertion tasks")

    plt.show()


def get_average_and_confidence(learning_times):
    confidence = 0.95
    intervals = []

    means = []
    std = []
    print(learning_times)
    for i in range(len(learning_times)):
        means.append(np.average(learning_times[i]))

    means, learning_times = (list(t) for t in zip(*sorted(zip(means, learning_times))))

    for i in range(len(learning_times)):
        std.append(np.std(learning_times[i]))
        interval = scipy.stats.t.interval(alpha=confidence, df=len(learning_times[i])-1,loc=means[i], scale=scipy.stats.sem(learning_times[i]))
        intervals.append((interval[1] - interval[0])/2)

    return np.asarray(means), np.asarray(intervals)


def get_learning_time(costs: list, learning_threshold: float, p: DataProcessor):
    learning_time_average = []
    for i in range(len(costs)):
        learning_time_average.append(get_learning_duration(np.asarray(costs[i]), learning_threshold))
        #learning_time_average.append(find_convergence(np.asarray(costs[i]),0.001))
    return learning_time_average


def get_learning_duration(cost: np.ndarray, threshold: float):
    if len(np.where(cost <= threshold)[0]) == 0:
        return len(cost)
    else:
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
        threads.append(Thread(target=call_method, args=(agent, 12000, cmd,)))
        threads[-1].start()

    for t in threads:
        t.join()


def teach_generic_insertable(agent: str):
    call_method(agent, 12000, "set_grasped_object", {"object": "generic_insertable"})
    input("Press Enter to teach the approach pose.")
    call_method(agent, 12000, "teach_object", {"object": "generic_approach"})
    input("Press Enter to teach the container pose.")
    call_method(agent, 12000, "teach_object", {"object": "generic_container"})


def benchmark_single_batchwise(agent: str,  unique_tag: str, n_tasks: int, n_iter: int = 1):

    delete_local_results([agent], "ml_results", "benchmark_rastrigin", ["collective_benchmark_single_batchwise"])
    delete_local_results([database], "collective_data", "benchmark_rastrigin", ["collective_benchmark_single_batchwise"])
    delete_local_knowledge([agent], "local_knowledge", "benchmark_rastrigin", ["benchmark_batchwise"])

    task_set = np.random.rand(n_tasks, 6).tolist()

    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.batch_width = base_batch_size_benchmark
    service_config.n_trials = n_trials_benchmark

    knowledge = {"mode": "local", "type": "predicted", "kb_location": agent, "scope": ["benchmark_batchwise"]}

    for i in range(n_iter):
        for j in range(len(task_set)):
            x0 = task_set[j]
            pd = mios_complex_ml_benchmark(x0, 10)
            pd.identity = x0
            tags = ["collective_benchmark_single_batchwise", unique_tag, "t_" + str(j)]
            start_single_experiment(agent, [agent], pd, service_config, i, tags, knowledge, False)

    backup_results(agent, database, "benchmark_rastrigin", ["collective_benchmark_single_batchwise", unique_tag], "collective_data")


def benchmark_single_batchwise_similar(agent: str,  unique_tag: str, n_tasks: int, n_iter: int = 1):

    delete_local_results([agent], "ml_results", "benchmark_rastrigin", ["collective_benchmark_single_batchwise_similar"])
    delete_local_results([database], "collective_data", "benchmark_rastrigin", ["collective_benchmark_single_batchwise_similar"])
    delete_local_knowledge([agent], "local_knowledge", "benchmark_rastrigin", ["benchmark_batchwise_similar"])

    task_set = np.random.rand(n_tasks, 6).tolist()

    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.batch_width = base_batch_size_benchmark
    service_config.n_trials = n_trials_benchmark

    knowledge = {"mode": "local", "type": "similar", "kb_location": agent, "scope": ["benchmark_batchwise_similar"]}

    for i in range(n_iter):
        for j in range(len(task_set)):
            x0 = task_set[j]
            pd = mios_complex_ml_benchmark(x0, 10)
            pd.identity = x0
            tags = ["collective_benchmark_single_batchwise_similar", unique_tag, "t_" + str(j)]
            start_single_experiment(agent, [agent], pd, service_config, i, tags, knowledge, False)

    backup_results(agent, database, "benchmark_rastrigin", ["collective_benchmark_single_batchwise_similar", unique_tag], "collective_data")


def experiment_single_batchwise_similar(agent: str,  unique_tag: str, n_tasks: int, n_iter: int = 1):
    delete_local_results([agent], "ml_results", "insertion", ["collective_experiment_single_batchwise_similar"])
    delete_local_results([database], "collective_data", "insertion", ["collective_experiment_single_batchwise_similar"])
    delete_local_knowledge([agent], "local_knowledge", "insertion", ["experiment_batchwise_similar"])

    call_method(agent, 12000, "set_grasped_object", {"object": "generic_insertable"})

    task_set = []

    for j in range(n_tasks):
        task_set.append([j*0.1, 1-j*0.1])

    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.batch_width = base_batch_size_experiment
    service_config.n_trials = n_trials_experiment

    knowledge = {"mode": "local", "type": "similar", "kb_location": agent, "scope": ["experiment_batchwise_similar"]}

    for i in range(n_iter):
        for j in range(len(task_set)):
            if j==0:
                knowledge = None
            pd = insert_generic()
            pd.cost_function.optimum_weights[0] = task_set[j][0]
            pd.cost_function.optimum_weights[2] = task_set[j][1]
            pd.identity = task_set[j]
            pd.identity_weights = [1, 1]
            tags = ["collective_experiment_single_batchwise_similar", unique_tag, "t_" + str(j)]
            start_single_experiment(agent, [agent], pd, service_config, i, tags, knowledge, False)

    backup_results(agent, database, "insertion", ["collective_experiment_single_batchwise_similar", unique_tag], "collective_data")


def plot_batch_data(unique_tag: str, db: str):
    p = DataProcessor()
    marker = "collective_experiment"
    skill = "insert_object"
    n_tasks = 10

    fig, axes = plt.subplots(n_tasks, 1)
    for i in range(n_tasks):
        tags = [marker + "_single_batchwise_similar", unique_tag, "t_" + str(i)]
        try:
            results = get_multiple_experiment_data(db, skill,
                                                          results_db="ml_results",
                                                          filter={"meta.tags": {"$all": tags}})
            cost, conf = p.get_average_cost_over_time(results, decreasing=True)
            axes[i].plot(cost)

        except DataNotFoundError:
            print("No data found for tags: " + str(tags))
            continue

    plt.show()



def plot_batch_data_comparison(unique_tag_single: str, unique_tag_shared: str, benchmark: bool = True):
    if benchmark is True:
        marker = "collective_benchmark"
        skill = "benchmark_rastrigin"
        learning_thresholds = benchmark_learning_thresholds
    else:
        marker = "collective_experiment"
        skill = "insert_object"
        learning_thresholds = experiment_learning_thresholds

    n_tasks = 10

    p = DataProcessor()

    knowledge_time_single = []

    for i in range(n_tasks):
        tags_single = [marker + "_single_batchwise", unique_tag_single, "t_" + str(i)]
        try:
            results_single = get_multiple_experiment_data(database, skill,
                                                   results_db="collective_data",
                                                   filter={"meta.tags": {"$all": tags_single}})
        except DataNotFoundError:
            print("No data found for tags: " + str(tags_single))
            continue

        knowledge_time_single.append(
            get_learning_time(p.get_collection_of_costs_over_time(results_single, decreasing=True), 0.008, p))

        print(knowledge_time_single)

    fig_knowledge, axes_knowledge = plt.subplots()

    knowledge_time_single_avg = np.average(knowledge_time_single,axis=1)

    for i in range(1, len(knowledge_time_single_avg)):
        knowledge_time_single_avg[i] += knowledge_time_single_avg[i - 1]

    knowledge_time_single_avg = np.insert(knowledge_time_single_avg, 0, 0)

    knowledge_units = np.linspace(0, len(knowledge_time_single_avg) - 1, len(knowledge_time_single_avg))

    axes_knowledge.plot(knowledge_time_single_avg, knowledge_units, "g")

    axes_knowledge.legend(("Single Learning", "Parallel Learning", "Collective Learning"))

    plt.xlabel("Time [s]")
    plt.ylabel("Tasks Learned [1]")
    plt.title("Knowledge acquisition for four insertion tasks")

    plt.show()


def find_convergence(cost: np.ndarray, interval: float = 0.05) -> int:
    for i in range(len(cost) - 1):
        in_interval = True
        for j in range(i + 1, len(cost)):
            if abs(cost[i] - cost[j]) <= interval:
                continue
            else:
                in_interval = False
        if in_interval is True:
            return i
    return len(cost) - 1


def var_agents_exp(agents: list, tags: list):
    for i in range(len(agents)):
        tags_tmp = tags.copy()
        tags_tmp.append("n_a_" + str(i+1))
        pd = InsertionFactory(agents[0:i+1], TimeMetric("insertion", {"time": 5}),
                              {"Insertable": "key_exp_key", "Container": "key_exp_container",
                               "Approach": "key_exp_approach"}).get_problem_definition("key_exp_key")
        sc = SVMLearner().get_configuration()
        start_experiment(agents[0], agents[0:i+1], pd, sc, 10, tags=tags_tmp, keep_record=False)


def plot_var_agents_exp(host_data: str, db_data: str, tags: list):
    p = DataProcessor()
    skill_class = "insertion"
    max_time = 1500
    fig, axes = plt.subplots(1, 1, sharex=True, sharey=False, gridspec_kw={'hspace': 0, 'wspace': 0})

    axes.set_xlim(0, 1500)
    axes.set_ylim(0, 10)
    axes.grid()
    axes.tick_params(axis="both", which="both", length=0)
    axes.set_title(skill_class, y=1.0, pad=-14)

    styles = ["solid", "dashed", "dotted", "dashdot", "dashed"]

    for i in range(5):
        tags_tmp = tags.copy()
        tags_tmp.append("n_a_" + str(i+1))

        try:
            results = get_multiple_experiment_data(host_data, skill_class, results_db=db_data,
                                                   filter={"meta.tags": {"$all": tags_tmp}})
        except (DataNotFoundError, DataError):
            print("Data for skill class " + skill_class + " and tags " + str(tags_tmp) + " does not exist on " +
                  host_data + " in database " + db_data)
            return False
        cost, confidence_cost = p.get_average_cost_over_time(results, 1500, True)
        cost = cost[0:1500] * 5
        confidence_cost = confidence_cost[0:1500] * 5
        casr, confidence_casr = p.get_average_success_over_time(results)
        casr = casr[0:1500]
        confidence_casr = confidence_casr[0:1500]

        for k in range(1, len(casr)):
            casr[k] += casr[k - 1]

        axes.plot(cost, linestyle=styles[i], zorder=2, linewidth=4)
        # axes[0].fill_between(np.linspace(0, len(cost), len(cost)), cost - confidence_cost,
        #                      cost + confidence_cost, alpha=0.2, color="blue")
        # axes[1].plot([0, len(casr)], [0, len(casr)], color="black", linestyle="dashed")
        # axes[1].plot(casr, linestyle="dashed", zorder=2, linewidth=4)
        # axes[1].fill_between(np.linspace(0, len(casr), len(casr)), casr - confidence_casr,
        #                      casr + confidence_casr, alpha=0.2)
    legend_cost = ["n_a=1", "n_a=2", "n_a=3", "n_a=4", "n_a=5"]
    legend_casr = ["Optimal CASR", skill_class]

    axes.legend(legend_cost, fontsize='x-small', loc=1)
    # axes[1].legend(legend_casr, fontsize='x-small', loc='upper left')

    ticks = np.linspace(2, 10, 5)
    axes.set_yticks(ticks)
    axes.set_yticklabels(list(map(str, ticks)))
    # ticks = np.linspace(250, max_time, 6)
    # axes[1].set_xticks(ticks)
    # axes[1].set_xticklabels(list(map(str, ticks)))
    # axes[1].tick_params(axis='both', which='major', labelsize=12)

    plt.show()
