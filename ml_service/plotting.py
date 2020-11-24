import numpy as np
from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor
from plotting.data_processor import DataError
from plotting.plotter import Plotter
import matplotlib.pyplot as plt


def single_experiment(host: str, task_type: str, database: str, tags: list = None, uuid: str = None):
    p = DataProcessor()
    plot = Plotter()
    if tags is not None:
        result = get_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags}})
    elif uuid is not None:
        result = get_experiment_data(host, task_type, results_db=database, uuid=uuid)
    else:
        return
    plot.plot_cost_over_trials(p.get_monotonically_decreasing_cost(result.get_cost_per_trial()))


def average_experiment(host: str, task_type: str, database: str, tags: list):
    p = DataProcessor()
    plot = Plotter()
    results = get_multiple_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost(results, True, 13)
    plot.plot_cost_over_trials(cost)


def plot_experiment(host: str, task_type: str, database: str, tags: list):
    p = DataProcessor()
    plot = Plotter()
    for i in range(10):
        try:
            tags_tmp = tags.copy()
            tags_tmp.append("n" + str(i+1))
            print(tags_tmp)
            result = get_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags_tmp}})
            plot.plot_cost_over_trials(p.get_monotonically_decreasing_cost(result.get_cost_per_trial()))
        except DataNotFoundError:
            pass


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


def plot_transfer_learning(db: str):
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", "key_abus_e30",
             "key_pad", "key_old", "key_hatch"]

    p = DataProcessor()
    fig, axes = plt.subplots(10, 10, sharex=True, sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0})
    for i in range(len(tasks)):
        for j in range(len(tasks)):
            axes[i, j].set_xlim(0, 130)
            axes[i, j].set_ylim(0, 1)
            axes[i, j].grid()
            axes[i, j].tick_params(axis="both", which="both", length=0)
            try:
                if i == j:
                    print("Processing plot " + str(i * 10 + j +1), end="\r")
                    tags = ["transfer_learning", tasks[i]]
                    results = get_multiple_experiment_data("collective-control-001.local", "insert_object", results_db="results_tl_base",
                                                           filter={"meta.tags": {"$all": tags}})
                    cost = p.get_average_cost(results, True)
                    axes[i, j].plot(cost)
                else:
                    tags = ["transfer_learning", tasks[j], "from_" + tasks[i]]
                    results = get_multiple_experiment_data("collective-control-001.local", "insert_object",
                                                           results_db=db,
                                                           filter={"meta.tags": {"$all": tags}})
                    cost = p.get_average_cost(results, True)
                    axes[i, j].plot(cost)
            except (DataNotFoundError, DataError):
                print("No data found for experiment (" + str(i) + "," + str(j) + ")")
            if i == 0:
                axes[i, j].annotate("t" + str(j), xy=(0.5, 1), xytext=(0, 5),
                            xycoords='axes fraction', textcoords='offset points',
                            size='large', ha='center', va='baseline')
            if j == 0:
                axes[i, j].annotate("t" + str(i), xy=(0, 0.5), xytext=(-axes[i, j].yaxis.labelpad - 5, 0),
                            xycoords=axes[i, j].yaxis.label, textcoords='offset points',
                            size='large', ha='right', va='center')
                axes[i ,j].set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1])
                axes[i, j].set_yticklabels([''] * 6)
            if i == len(tasks) - 1:
                axes[i, j].set_xticks([0, 25, 50, 75, 100])
                axes[i, j].set_xticklabels(["0", "", "50", "", "100"])
    fig.add_subplot(111, frame_on=False)
    plt.tick_params(labelcolor="none", bottom=False, left=False)
    plt.xlabel("Trial [1]")
    plt.ylabel("Normed execution time [s/10]")
    plt.show()


def plot_transfer_learning_2(task: str):
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", "key_pad", "key_hatch", "key_old"]
    p = DataProcessor()
    plot = Plotter()
    tags = ["transfer_learning", task]
    results = get_multiple_experiment_data("collective-control-001.local", "insert_object", results_db="transfer_base_v2",
                                           filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost(results, True, 13)
    cost = np.insert(cost, 0, 1)
    plot.plot_cost_over_trials(cost)
    legend = [task]
    for i in range(len(tasks)):
        try:
            tags = ["transfer_learning", task, "from_" + tasks[i]]
            results = get_multiple_experiment_data("collective-control-001.local", "insert_object",
                                                   results_db="transfer_all_v2",
                                                   filter={"meta.tags": {"$all": tags}})
            cost = p.get_average_cost(results, True, 13)
            cost = np.insert(cost, 0, 1)
            plt.plot(cost)
            legend.append(tasks[i])
        except (DataNotFoundError, DataError):
            print("No data found for experiment (" + str(i) + ")")


    plt.ylabel("Normed execution time [s/10]")
    plt.xlabel("Episodes [1]")
    plt.grid()
    plt.legend(legend)
    plt.title("Knowledge transfer for task " + task)
    plt.show()


def plot_transfer_learning_3():
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60",
             "key_pad", "key_old", "key_hatch"]

    n_cols = 3
    n_rows = 3

    speedup_matrix = np.zeros((len(tasks), len(tasks)))
    le_ratio_matrix = np.zeros((len(tasks), len(tasks)))

    p = DataProcessor()
    fig, axes = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0})
    for i in range(n_rows):
        for j in range(n_cols):
            axes[i, j].set_xlim(0, 10)
            axes[i, j].set_ylim(0, 1)
            axes[i, j].grid()
            axes[i, j].tick_params(axis="both", which="both", length=0)
            legend = []
            try:
                tags = ["transfer_learning", tasks[i * n_rows + j]]
                results = get_multiple_experiment_data("collective-control-001.local", "insert_object",
                                                       results_db="transfer_base_v2",
                                                       filter={"meta.tags": {"$all": tags}})
                base_cost = p.get_average_cost(results, True, 13)
                base_cost = np.insert(base_cost, 0, 1)
                axes[i, j].plot(base_cost)
                legend = [tasks[i * n_rows + j]]
            except (DataNotFoundError, DataError):
                print("Base cost for task " + tasks[i] + " not found.")
                continue
            for t in range(len(tasks)):
                try:
                    tags = ["transfer_learning", tasks[i * n_rows +j], "from_" + tasks[t]]
                    results = get_multiple_experiment_data("collective-control-001.local", "insert_object",
                                                           results_db="transfer_all_v2",
                                                           filter={"meta.tags": {"$all": tags}})
                    cost = p.get_average_cost(results, True, 13)
                    cost = np.insert(cost, 0, 1)

                    if base_cost[-1] < cost[-1]:
                        baseline = base_cost[-1]
                    else:
                        baseline = cost[-1]

                    le_base = np.sum(base_cost) - baseline
                    le_transfer = np.sum(cost) - baseline
                    le_ratio_matrix[i * n_rows + j][t] = le_transfer / le_base

                    index_thr_base_cost = find_convergence(base_cost, 0.025)
                    thr_base_cost = base_cost[index_thr_base_cost]
                    index_thr_transfer_cost = np.where(cost < thr_base_cost)
                    if index_thr_transfer_cost[0].size == 0:
                        index_thr_transfer_cost = 1
                        index_thr_base_cost = 1
                    else:
                        index_thr_transfer_cost = index_thr_transfer_cost[0][0]

                    axes[i, j].plot(cost)
                    speedup_matrix[i * n_rows + j][t] = index_thr_base_cost / index_thr_transfer_cost

                    legend.append("from_" + tasks[t])
                except (DataNotFoundError, DataError):
                    pass

            axes[i, j].legend(legend, fontsize='xx-small', loc=1)
            # if i == 0:
            #     pass
            #     axes[i, j].annotate("t" + str(j), xy=(0.5, 1), xytext=(0, 5),
            #                         xycoords='axes fraction', textcoords='offset points',
            #                         size='large', ha='center', va='baseline')
            # if j == 0:
            #     pass
            #     axes[i, j].annotate("t" + str(i), xy=(0, 0.5), xytext=(-axes[i, j].yaxis.labelpad - 5, 0),
            #                         xycoords=axes[i, j].yaxis.label, textcoords='offset points',
            #                         size='large', ha='right', va='center')
            #     axes[i, j].set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1])
            #     axes[i, j].set_yticklabels([''] * 6)
            if i == n_rows - 1:
                axes[i, j].set_xticks([2, 4, 6, 8, 10])
                axes[i, j].set_xticklabels(["2", "4", "6", "8", "10"])
    fig.add_subplot(111, frame_on=False)
    plt.tick_params(labelcolor="none", bottom=False, left=False)
    plt.xlabel("Trial [1]")
    plt.ylabel("Normed execution time [s/10]")

    es_matrix = np.zeros(le_ratio_matrix.shape)
    for i in range(le_ratio_matrix.shape[0]):
        for j in range(le_ratio_matrix.shape[1]):
            if le_ratio_matrix[i, j] > 0:
                es_matrix[i, j] = np.min([le_ratio_matrix[i, i] / le_ratio_matrix[i, j], 1])

    print(es_matrix)
    print(speedup_matrix)

    header = np.array(["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9"])

    es_matrix = es_matrix.astype('|S4')
    speedup_matrix = speedup_matrix.astype('|S4')

    es_matrix = np.vstack((header, es_matrix))
    speedup_matrix = np.vstack((header, speedup_matrix))

    header = np.insert(header, 0, "")

    es_matrix = np.hstack((header.reshape(-1,1), es_matrix))
    speedup_matrix = np.hstack((header.reshape(-1, 1), speedup_matrix))

    np.savetxt("es_matrix.csv", es_matrix, delimiter=",", fmt="%s")
    np.savetxt("speedup_matrix.csv", speedup_matrix, delimiter=",", fmt="%s")
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


def count_transfer_learning(host: str, db: str, task_type: str):
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", "key_abus_e30",
             "key_pad", "key_old", "key_hatch"]
    client = MongoDBClient(host)
    for t1 in tasks:
        for t2 in tasks:
            docs = client.read(db, task_type, {"meta.tags": {"$all": ["transfer_learning", t1, "from_" + t2]}})
            if len(docs) != 10:
                print("Experiment with tags [" + t1 + ", " + t2 + "] has " + str(len(docs)) + " documents.")


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
