import numpy as np
from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor
from plotting.plotter import Plotter


def single_experiment(host: str, task_type: str, uuid: str):
    p = DataProcessor()
    plot = Plotter()
    result = get_experiment_data(host, task_type, uuid=uuid)
    plot.plot_cost_over_trials(p.get_monotonically_decreasing_cost(result.get_cost_per_trial()))


def average_experiment(host: str, task_type: str, database: str, tags: list):
    p = DataProcessor()
    plot = Plotter()
    results = get_multiple_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost(results, True)
    plot.plot_cost_over_trials(cost)


def agent_learning(tags, hosts = ["collective-panda-002.local"]):
    filter = {"meta.tags": tags}
    knowledge_mode = "global"
    # task_type = "insert_object"
    task_type = "benchmark_rastrigin"

    p = DataProcessor()
    plot = Plotter()
    results = []
    for host in hosts:
        results.extend(get_multiple_experiment_data(host, task_type, knowledge_mode, filter=filter))

    results = p.sort_over_time(results)
    agent_results = p.get_agent_results(results)  # seperate results for every agent
    for agent, agent_results in agent_results.items():
        agent_times_cum = p.get_cumulative_time(agent_results)
        plot.plot_learning_over_task(agent_times_cum, agent)


def global_learning(tags, hosts = ["collective-panda-002.local"]):
    filter = {"meta.tags": tags}
    knowledge_mode = "global"
    # task_type = "insert_object"
    task_type = "benchmark_rastrigin"

    p = DataProcessor()
    plot = Plotter()
    results = []
    for host in hosts:
        results.extend(get_multiple_experiment_data(host, task_type, knowledge_mode, filter=filter))

    results = p.sort_over_time(results)
    all_times = p.get_cumulative_time(results)
    plot.plot_learning_over_task(all_times, "global")
