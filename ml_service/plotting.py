from math import isclose, ceil
from sys import exception
import numpy as np
import copy
from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor
from plotting.data_processor import DataError
from plotting.plotter import Plotter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d import Axes3D
import csv
from pymongo.errors import ServerSelectionTimeoutError
import scipy.stats as st
from matplotlib import colors
import seaborn as sns
import pickle

plot = Plotter()

list_block_1 = ["001", #"002", 
                "003", "004", "005", 
                "006", "007", "008", "044", 
                "011", "012"]
list_block_2 = ["043","013","014","015","016","042",
                "041",#"020",
                "021","022"]
list_U = ["023", "024", "025", "026","047", "040", "029"] #, , "028"
list_external = ["050"]
cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
            '003_left': 0.68016,
            '004_left': 0.74976,
            '005_left': 0.65, #
            '006_left': 0.6127199999999999,
            '007_left': 0.62616,
            '008_left': 0.6371999999999999,
            '010_left': 0.6888000000000001,
            '011_left': 0.63816,
            '012_left': 0.75528,
            '009_left': 0.6943199999999999,
            '013_left': 0.6348,
            '014_left': 0.6,
            '015_left': 0.68184,
            '016_left': 0.9,   #
            '017_left': 0.63864,
            '041_left': 0.63144,  # '018_left': 0.63144,09
            '021_left': 0.63528,
            '022_left': 0.6828000000000001,
            '023_left': 0.6648000000000001,
            '024_left': 0.9187199999999999,
            '025_left': 0.64752,
            '027_left': 0.68448,
            '028_left': 0.61824,
            '029_left': 0.68088}

def check_cutoff():
    tags = ["test", "CMAEStest"]
    for m in list_block_1+list_block_2+list_U:
        results = get_multiple_experiment_data("collective-"+m+".rsi.ei.tum.de", "insertion", "ml_results", filter={"meta.tags": {"$all": tags}})
        for r in results:
            print(r.tags)
            undercuts = sum([1 for i in r.costs if i < cutoff[m+"_left"]])
            print(m, "performed better than", cutoff[m+"_left"], " for ", undercuts, "times")


def plot_single_experiment(host: str, task_type:str = "insertion", database:str = "ml_results", tags: list = None, uuid: str = None):
    p = DataProcessor()

    if tags is not None:
        result = get_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags}})
    elif uuid is not None:
        result = get_experiment_data(host, task_type, results_db=database, uuid=uuid)
    else:
        return
    cost, confidence = result.get_cost_per_time()
    cost_mono = p.get_monotonically_decreasing_cost(cost)

    plt.plot(cost)
    plt.ylim((0, 10))
    plt.show()
    # plot.plot_cost_over_trials())


def average_experiment(host: str, task_type: str, database: str, tags: list, agent=None):
    p = DataProcessor()

    results = get_multiple_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags}})
    # cost = p.get_average_cost_over_time(results, 1500, True)
    cost, confidence = p.get_average_cost(results, True, 1, agent)
    plt.plot(cost)
    plt.ylim([0, 2.5])
    plt.show()


def plot_experiment(host: str, skill_class: str, database: str, tags: list, max_cost: int, cost_function: str):
    p = DataProcessor()

    results = get_multiple_experiment_data(host, skill_class, results_db=database, filter={"meta.tags": {"$all": tags}})
    cost, confidence = p.get_average_cost_over_time(results, False, True)
    plt.fill_between(np.linspace(0, len(cost), len(cost)), cost - confidence, cost + confidence, alpha=0.2)
    plt.plot(cost, linewidth=2)
    plt.plot([0, len(cost)], [max_cost, max_cost], color="black", linestyle="dashed")
    plt.plot(cost)
    plt.ylim([0, max_cost * 2])
    plt.ylabel(cost_function)
    plt.xlabel("Time [s]")
    plt.show()


def agent_learning(tags, hosts=["collective-panda-002.local"]):
    filter = {"meta.tags": tags}
    knowledge_mode = "global"
    task_type = "insert_object"
    # task_type = "benchmark_rastrigin"

    p = DataProcessor()

    results = []
    for host in hosts:
        results.extend(get_multiple_experiment_data(host, task_type, "global_ml_results", filter=filter))

    results = p.sort_over_time(results)
    agent_results = p.get_agent_results(results)  # seperate results for every agent
    for agent, agent_results in agent_results.items():
        agent_times_cum = p.get_cumulative_time(agent_results)
        plot.plot_learning_over_task(agent_times_cum, agent)


def ler_explanation2(host: str, db: str, tags: list):
    skill_class = "insert_object"
    min_length = 1500
    p = DataProcessor()
    # first leaning curve
    results_a = get_multiple_experiment_data(host, skill_class, results_db=db, filter={"meta.tags": tags})[0]
    cost, time = results_a.get_cost_per_time()
    cost = [c * 10 / 10 for c in cost]

    plt.plot(time, cost, color="blue", linestyle="solid", label="Cost function", linewidth=0.85)
    cost_dec = p.get_monotonically_decreasing_cost(cost)
    plt.plot(time, cost_dec, color="red", linestyle="dashed", label="Monotonically decreasing cost function")

    plt.xlim(0, 1400)
    plt.ylim(0, 1)
    plt.ylabel("Cost []", fontsize=12)
    plt.xlabel("Learning Time [s]", fontsize=12)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(loc=1, fontsize=12)
    plt.gcf().set_size_inches(5, 3)
    plt.savefig("cost_explain.png", bbox_inches='tight', dpi=600)  # , pad_inches = 0
    plt.show()


def ler_explanation(host, tags_a, tags_b):
    task_type = "insert_object"
    database_a = "transfer_all_v2"
    database_b = "transfer_all_v2"
    min_length = 1500
    p = DataProcessor()
    # first leaning curve
    results_a = get_multiple_experiment_data(host, task_type, results_db=database_a, filter={"meta.tags": tags_a})[0]
    print("len results_a", len(results_a.trials))
    cost_a, time_a = results_a.get_cost_per_time()
    cost_a = [c * 10 / 10 for c in cost_a]
    print("len cost_a, time_a", len(cost_a), len(time_a))

    plt.plot(time_a, cost_a, color="blue", linestyle="solid", label="Cost function (task A)", linewidth=0.85)
    cost_a_dec = p.get_monotonically_decreasing_cost(cost_a)
    plt.plot(time_a, cost_a_dec, color="red", linestyle="dashed", label="Monocally decreasing cost function (task A)")
    plt.fill_between(time_a, cost_a_dec, facecolor="#e3e8ff", zorder=0, interpolate=True,
                     label="LE task A")  # , hatch = "///"
    # second learning curve
    results_b = get_multiple_experiment_data(host, task_type, results_db=database_b, filter={"meta.tags": tags_b})[0]
    cost_b, time_b = results_b.get_cost_per_time()
    cost_b = [c * 10 / 10 for c in cost_b]
    cost_b_dec = p.get_monotonically_decreasing_cost(cost_b)
    plt.plot(time_b, cost_b_dec, color="green", linestyle="dotted", label="Monocally decreasing cost function (task B)")
    # plt.fill_between(time_b, cost_b_dec, color="#ffffff", zorder=1, interpolate=True)
    plt.fill_between(time_b, cost_b_dec, facecolor="#ffd2b0", zorder=2, label="LE task B")  # , hatch = "\\\\"

    # additional stuff
    # red bar
    plt.plot([time_b[-1], time_b[-1] + 20], [cost_b[-1], cost_b[-1]], color='r')
    plt.plot([time_b[-1], time_b[-1] + 20], [0, 0], color='r')
    plt.plot([time_b[-1] + 10, time_b[-1] + 10], [cost_b[-1], 0], color='r', label="b")

    plt.xlim(0, 1400)
    plt.ylim(0, 1)
    plt.ylabel("Cost []", fontsize=12)
    plt.xlabel("Learning Time [s]", fontsize=12)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(loc=1, fontsize=12)
    plt.gcf().set_size_inches(8, 5)
    plt.savefig("ler_explain.png", bbox_inches='tight', dpi=600)  # , pad_inches = 0
    plt.show()


def plot_collective_learning(tags, data_src):
    filter = {"meta.tags": tags}
    knowledge_mode = "global"
    task_type = "insert_object"
    # task_type = "benchmark_rastrigin"

    p = DataProcessor()

    results = []
    results.extend(get_multiple_experiment_data(data_src, task_type, "global_ml_results", filter=filter))
    results = p.sort_over_time(results)

    times = p.get_cumulative_time(results)
    times = np.insert(times, 0, 0)
    tasks = np.linspace(0, len(times), len(times + 1))
    plt.plot(times, tasks)
    plt.show()


def plot_transfer_learning(db: str):
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", #"key_abus_e30",
             "key_pad", "key_old", "key_hatch"]
    tasks = ["cylinder_50", "usb-a", "schuko", "IEC60320_C13", "abus_e30"]

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
                    print("Processing plot " + str(i * 10 + j + 1), end="\r")
                    tags = ["transfer_learning", tasks[i]]
                    results = get_multiple_experiment_data("collective-020", "insertion",  # collective-control-001.local , insert_object
                                                           results_db="global_ml_results",
                                                           filter={"meta.tags": {"$all": tags+["base"]}})
                    cost = p.get_average_cost(results, True)
                    axes[i, j].plot(cost)
                else:
                    tags = ["transfer_learning", tasks[j], "from_" + tasks[i]]
                    results = get_multiple_experiment_data("collective-020", "insertion",  # collective-control-001.local, insert_object
                                                           results_db="global_ml_results",
                                                           filter={"meta.tags": {"$all": tags}})
                    cost = p.get_average_cost(results, True)
                    axes[i, j].plot(cost)
            except (DataNotFoundError, DataError):
                print("No data found for experiment (" + str(i) + "," + str(j) + "): ",tasks[j],", from_",tasks[i])
            if i == 0:
                axes[i, j].annotate("t" + str(j), xy=(0.5, 1), xytext=(0, 5),
                                    xycoords='axes fraction', textcoords='offset points',
                                    size='large', ha='center', va='baseline')
            if j == 0:
                axes[i, j].annotate("t" + str(i), xy=(0, 0.5), xytext=(-axes[i, j].yaxis.labelpad - 5, 0),
                                    xycoords=axes[i, j].yaxis.label, textcoords='offset points',
                                    size='large', ha='right', va='center')
                axes[i, j].set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1])
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
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", "key_pad",
             "key_hatch", "key_old"]
    tasks = ["cylinder_50", "usb-a", "schuko", "IEC60320_C13", "abus_e30"]
    p = DataProcessor()
    plot = Plotter()
    tags = ["transfer_learning", task]
    results = get_multiple_experiment_data("collective-020", "insertion",  # collective-control-001.local
                                           results_db="global_ml_results",  #"transfer_base_v2",
                                           filter={"meta.tags": {"$all": tags+["base"]}})
    cost = p.get_average_cost(results, True, 13)
    cost = np.insert(cost, 0, 1)
   # plot.plot_cost_over_trials(cost)
    legend = [task]
    for i in range(len(tasks)):
        try:
            tags = ["transfer_learning", task, "from_" + tasks[i]]
            results = get_multiple_experiment_data("collective-020", "insertion",  # collective-control-001.local
                                                   results_db="global_ml_results", #  "transfer_all_v2",
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
    plt.xlim([0, 10])
    plt.ylim([0, 1])
    plt.show()


def plot_transfer_learning_3():
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60",
             "key_pad", "key_old", "key_hatch"]
    tasks = ["cylinder_50", "usb-a", "schuko", "IEC60320_C13", "abus_e30"]
    task_colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]

    n_cols = 2
    n_rows = 3

    episode_wise = False
    trial_wise = False
    if episode_wise is True:
        episode_size = 13
    else:
        episode_size = 1

    speedup_matrix = np.zeros((len(tasks), len(tasks)))
    le_ratio_matrix = np.zeros((len(tasks), len(tasks)))
    kl_matrix = np.zeros((len(tasks), len(tasks)))
    casr_matrix = np.zeros((len(tasks), len(tasks)))

    p = DataProcessor()
    fig, axes = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0})
    fig_casr, axes_casr = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0})
    fig.set_size_inches(16, 9)
    for i in range(n_rows):
        for j in range(n_cols):
            if i * n_cols + j > 4:
                continue
            if trial_wise is True:
                if episode_wise is True:
                    axes[i, j].set_xlim(0, 10)
                else:
                    axes[i, j].set_xlim(0, 130)
            else:
                axes[i, j].set_xlim(0, 1500)
            axes[i, j].set_ylim(0, 3)
            axes_casr[i, j].set_ylim(0, 1500)
            axes[i, j].grid()
            axes[i, j].tick_params(axis="both", which="both", length=0)
            axes[i, j].set_title(tasks[i * n_cols + j], y=1.0, pad=-14)
            legend = []
            try:
                tags = ["transfer_learning", tasks[i * n_cols + j]]
                results = get_multiple_experiment_data("collective-020","insertion",  #"localhost", "insert_object",
                                                       results_db="global_ml_results", #"transfer_base_v2",
                                                       filter={"meta.tags": {"$all": tags+["base"]}})
                if trial_wise is True:
                    base_cost, _ = p.get_average_cost(results, True, episode_size)
                    base_casr, _ = p.get_average_success(results)
                else:
                    base_cost, _ = p.get_average_cost_over_time(results, 1500, True)
                    base_cost = base_cost[0:1500]
                    base_casr, _ = p.get_average_success_over_time(results)
                    base_casr = base_casr[0:1500]
                base_cost = np.insert(base_cost, 0, 10)
                base_cost = base_cost * 10
                base_cost_log = np.log10(base_cost + 1)
                time_log = []
                for k in range(len(base_cost_log)):
                    time_log.append(np.log(k))
                base_casr = np.insert(base_casr, 0, 0)

                for k in range(1, len(base_casr)):
                    base_casr[k] += base_casr[k - 1]

                axes[i, j].plot(base_cost_log, linestyle="dashed", zorder=2, linewidth=4)
                axes_casr[i, j].plot([0, len(base_casr)], [0, len(base_casr)], color="black", linestyle="dashed")
                axes_casr[i, j].plot(base_casr, linestyle="dashed", zorder=2, linewidth=4)
                legend = [tasks[i * n_cols + j]]
                legend_casr = ["Optimal CASR", tasks[i * n_cols + j]]
            except (DataNotFoundError, DataError):
                print("Base cost for task " + tasks[i] + " not found.")
                continue
            for t in range(len(tasks)):
                try:
                    tags = ["transfer_learning", tasks[i * n_cols + j], "from_" + tasks[t]]
                    results = get_multiple_experiment_data("collective-020","insertion",  #"localhost", "insert_object",
                                                       results_db="global_ml_results", #"transfer_all_v2",
                                                       filter={"meta.tags": {"$all": tags}})
                    if trial_wise is True:
                        cost, _ = p.get_average_cost(results, True, episode_size)
                        casr, _ = p.get_average_success(results)
                    else:
                        cost, _ = p.get_average_cost_over_time(results, 1500, True)
                        cost = cost[0:1500]
                        casr, _ = p.get_average_success_over_time(results)
                        casr = casr[0:1500]
                    cost = np.insert(cost, 0, 10)
                    cost = cost * 10
                    cost_log = np.log10(cost + 1)
                    casr = np.insert(casr, 0, 0)

                    for k in range(1, len(casr)):
                        casr[k] += casr[k - 1]

                    if trial_wise is False:
                        baseline_factor = 1500
                    else:
                        if episode_wise is True:
                            baseline_factor = 10
                        else:
                            baseline_factor = 130
                    if base_cost[-1] < cost[-1]:
                        baseline = base_cost[-1] * baseline_factor
                    else:
                        baseline = cost[-1] * baseline_factor

                    le_base = np.sum(base_cost) - baseline
                    le_transfer = np.sum(cost) - baseline
                    le_ratio_matrix[i * n_cols + j][t] = le_transfer / le_base
                    kl_matrix[i * n_cols + j][t] = calculate_kl_divence(base_cost, cost)
                    casr_matrix[i * n_cols + j][t] = np.sum(casr) / np.sum(base_casr)

                    speedup_matrix[i * n_cols + j][t] = calculate_speedup(base_cost, cost)
                    axes[i, j].plot(cost_log, zorder=1, color=task_colors[t])
                    axes_casr[i, j].plot(casr, zorder=1, color=task_colors[t])

                    legend.append("from_" + tasks[t])
                    legend_casr.append("from_" + tasks[t])
                except (DataNotFoundError, DataError):
                    pass

            axes[i, j].legend(legend, fontsize='x-small', loc=1)
            axes_casr[i, j].legend(legend_casr, fontsize='x-small', loc='upper left')
            # if i == 0:
            #     pass
            #     axes[i, j].annotate("t" + str(j), xy=(0.5, 1), xytext=(0, 5),
            #                         xycoords='axes fraction', textcoords='offset points',
            #                         size='large', ha='center', va='baseline')
            if j == 0:
                axes[i, j].set_yticks([2, 4, ])#6, 8, 10])
                axes[i, j].set_yticklabels(["2", "4",])# "6", "8", "10"])
            #     pass
            #     axes[i, j].annotate("t" + str(i), xy=(0, 0.5), xytext=(-axes[i, j].yaxis.labelpad - 5, 0),
            #                         xycoords=axes[i, j].yaxis.label, textcoords='offset points',
            #                         size='large', ha='right', va='center')
            #     axes[i, j].set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1])
            #     axes[i, j].set_yticklabels([''] * 6)
            if i == n_rows - 1:
                if trial_wise is True:
                    if episode_wise is True:
                        axes[i, j].set_xticks([2, 4, 6, 8, 10])
                        axes[i, j].set_xticklabels(["2", "4", "6", "8", "10"])
                    else:
                        axes[i, j].set_xticks([25, 50, 75, 100, 130])
                        axes[i, j].set_xticklabels(["25", "50", "75", "100", "130"])
                        axes_casr[i, j].set_xticks([25, 50, 75, 100, 130])
                        axes_casr[i, j].set_xticklabels(["25", "50", "75", "100", "130"])
                else:
                    axes[i, j].set_xticks([250, 500, 750, 1000, 1250, 1500])
                    axes[i, j].set_xticklabels(["250", "500", "750", "1000", "1250", "1500"])
                    axes_casr[i, j].set_xticks([250, 500, 750, 1000, 1250, 1500])
                    axes_casr[i, j].set_xticklabels(["250", "500", "750", "1000", "1250", "1500"])
            axes[i, j].tick_params(axis='both', which='major', labelsize=12)
            axes_casr[i, j].tick_params(axis='both', which='major', labelsize=12)
    ax = fig.add_subplot(111, frame_on=False)
    ax_casr = fig_casr.add_subplot(111, frame_on=False)
    ax.tick_params(labelcolor="none", bottom=False, left=False)
    ax_casr.tick_params(labelcolor="none", bottom=False, left=False)
    if trial_wise is True:
        if episode_wise is True:
            ax.set_xlabel("Episode [1]")
            ax_casr.set_xlabel("Episode [1]")
        else:
            ax.set_xlabel("Trial [1]")
            ax_casr.set_xlabel("Episode [1]")
    else:
        ax.set_xlabel("Time [s]", fontsize=12)
        ax_casr.set_xlabel("Time [s]")
    ax.set_ylabel("Execution time [s]", fontsize=12)
    ax_casr.set_ylabel("CASR [1]", fontsize=12)

    fig.set_size_inches(16, 9)
    fig_casr.set_size_inches(16, 9)
    #fig.savefig("results_cost.png", bbox_inches='tight', dpi=300)
    fig_casr.savefig("results_casr.png", bbox_inches='tight', dpi=300)

    es_matrix = np.zeros(le_ratio_matrix.shape)
    for i in range(le_ratio_matrix.shape[0]):
        for j in range(le_ratio_matrix.shape[1]):
            if le_ratio_matrix[i, j] > 0:
                es_matrix[i, j] = np.min([le_ratio_matrix[i, i] / le_ratio_matrix[i, j], 1])

    print(es_matrix)
    print(speedup_matrix)
    print(le_ratio_matrix)
    print(kl_matrix)
    print(casr_matrix)

    header = np.array(["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9"])
    header = np.array(tasks)

    es_matrix = es_matrix.astype('|S4')
    speedup_matrix = speedup_matrix.astype('|S4')
    le_ratio_matrix = le_ratio_matrix.astype('|S4')
    casr_matrix = casr_matrix.astype('|S4')

    es_matrix = np.vstack((header, es_matrix))
    speedup_matrix = np.vstack((header, speedup_matrix))
    le_ratio_matrix = np.vstack((header, le_ratio_matrix))
    casr_matrix = np.vstack((header, casr_matrix))

    header = np.insert(header, 0, "")

    es_matrix = np.hstack((header.reshape(-1, 1), es_matrix))
    speedup_matrix = np.hstack((header.reshape(-1, 1), speedup_matrix))
    le_ratio_matrix = np.hstack((header.reshape(-1, 1), le_ratio_matrix))
    casr_matrix = np.hstack((header.reshape(-1, 1), casr_matrix))

    np.savetxt("es_matrix.csv", es_matrix, delimiter=",", fmt="%s")
    np.savetxt("speedup_matrix.csv", speedup_matrix, delimiter=",", fmt="%s")
    np.savetxt("ler_matrix.csv", le_ratio_matrix, delimiter=",", fmt="%s")
    np.savetxt("casr_matrix.csv", casr_matrix, delimiter=",", fmt="%s")
    plt.show()


color_level_0 = "#007474"
color_level_1 = "#0e5477"
color_level_2 = "#54b4d3"


def plot_transfer_learning_4():
    plt.rcParams.update({
        "text.usetex": True,
        'text.latex.preamble': r'\usepackage{amssymb}\usepackage{amsmath}\usepackage{mathbbol}',  # [r'\usepackage{amssymb}',r'\usepackage{amsmath}',r'\usepackage{mathbbol}']
        "font.family": 'serif',
        "font.size": 16
    })
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60",
             "key_pad", "key_old", "key_hatch"]
    tasks = ["cylinder_50", "usb-a", "schuko", "IEC60320_C13", "abus_e30"]

    task_colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]

    best_task = {
        "cylinder_10": "cylinder_20",
        "cylinder_20": "cylinder_10",
        "cylinder_30": "cylinder_10",
        "cylinder_40": "cylinder_60",
        "cylinder_50": "cylinder_40",
        "cylinder_60": "cylinder_30",
        "key_pad": "cylinder_10",
        "key_old": "key_pad",
        "key_hatch": "key_pad",
    }

    task_title = {
        "cylinder_10": r"$\mathbb{t}_1$",
        "cylinder_20": r"$\mathbb{t}_2$",
        "cylinder_30": r"$\mathbb{t}_3$",
        "cylinder_40": r"$\mathbb{t}_4$",
        "cylinder_50": r"$\mathbb{t}_5$",
        "cylinder_60": r"$\mathbb{t}_6$",
        "key_pad": r"$\mathbb{t}_7$",
        "key_old": r"$\mathbb{t}_8$",
        "key_hatch": r"$\mathbb{t}_9$",
    }
    task_title = {"cylinder_50":r"$\mathbb{t}_{cylinder_{50}}$",
                   "usb-a":r"$\mathbb{t}_{USB Tpye-A}$",
                "schuko":r"$\mathbb{t}_{schuko}$", 
                "IEC60320_C13":r"$\mathbb{t}_{IEC60320-C13}$", 
                "abus_e30":r"$\mathbb{t}_{abus-e30}$"}

    n_cols = 2
    n_rows = 3  # 3

    general_objects = True
    episode_wise = False
    trial_wise = False  # False
    if episode_wise is True:
        episode_size = 13
    else:
        episode_size = 1

    p = DataProcessor()
    fig, axes = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0})
    fig_casr, axes_casr = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0})
    fig.set_size_inches(16, 9)

    fig_dcasr, axes_dcasr = plt.subplots()

    dcasr_set = [[],[],[],[],[],[],[],[],[]]

    for i in range(n_rows):
        for j in range(n_cols):
            if i*n_cols+j>4:  # just for the evaluation plot
                continue
            if trial_wise is True:
                if episode_wise is True:
                    axes[i, j].set_xlim(0, 10)
                else:
                    axes[i, j].set_xlim(0, 130)
            else:
                axes[i, j].set_xlim(1, np.log10(1500))
                axes_casr[i, j].set_xlim(0, 7)
            axes[i, j].set_ylim(0, 1.2)
            axes_casr[i, j].set_ylim(0, 1)
            axes[i, j].grid()
            axes[i, j].tick_params(axis="both", which="both", length=0)
            axes[i, j].set_title("Task: " + task_title[tasks[i * n_cols + j]], x=0.1, y=0.13, pad=-14, fontsize=16)
            axes_casr[i, j].set_title("Task: " + task_title[tasks[i * n_cols + j]], y=1.0, pad=-14, fontsize=16)
            try:
                tags = ["transfer_learning", tasks[i * n_cols + j]]
                results = get_multiple_experiment_data("collective-020", "insertion",
                                                       results_db="global_ml_results",  #"transfer_base_v2",
                                                       filter={"meta.tags": {"$all": tags+["base"]}})
                if trial_wise is True:
                    base_cost, _ = p.get_average_cost(results, True, episode_size)
                    base_casr, _ = p.get_average_success(results)
                else:
                    base_cost, _ = p.get_average_cost_over_time(results, 1500, True)
                    base_cost = base_cost[0:1500]
                    base_casr, _ = p.get_average_success_over_time(results)
                    base_casr = base_casr[0:1500]
                base_cost = np.insert(base_cost, 0, 10)
                base_cost = base_cost * 10
                base_casr = np.insert(base_casr, 0, 0)
                base_dcasr = np.diff(base_casr)
                dcasr_set[i * n_rows + j].append(base_dcasr)
                base_cost_log = np.log10(base_cost + 1)
                time_log = []
                print(base_cost)
                for k in range(len(base_cost_log)):
                    time_log.append(np.log10(k))
                if len(base_casr) < 1500:
                    base_casr = np.pad(base_casr, ((0, 1500 - len(base_casr))), mode='constant',
                                       constant_values=np.mean(base_casr[len(base_casr) - 100:]))

                for k in range(1, len(base_casr)):
                    base_casr[k] += base_casr[k - 1]

                axes[i, j].plot(time_log, base_cost_log, linestyle="solid", zorder=2, label='None-Transfer', linewidth=2)
                # axes_casr[i, j].plot([0, len(base_casr)], [0, len(base_casr)], linewidth=1, color="gray", linestyle="solid")
                base_asr_mean, base_asr_std = get_mean_over_window(np.diff(base_casr))
                axes_casr[i, j].stairs(base_asr_mean, linestyle="solid", zorder=2, label="None-Transfer", linewidth=2)
                #legend = ["None-Transfer"]
                #legend_casr = ["Optimal CALSC", "Raw Learning"]
            except (DataNotFoundError, DataError):
                print("Base cost for task " + tasks[i] + " not found.", i,j)
                continue

            cost_cylinders = []
            casr_cylinders = []
            cost_keys = []
            casr_keys = []
            cost_general_object = []
            casr_general_object = []
            for t in range(len(tasks)):
                try:
                    tags = ["transfer_learning", tasks[i * n_cols + j], "from_" + tasks[t]]
                    results = get_multiple_experiment_data("collective-020","insertion",  #"localhost", "insert_object",
                                                           results_db="global_ml_results",  # "transfer_all_v2",
                                                           filter={"meta.tags": {"$all": tags}})
                    if trial_wise is True:
                        cost, _ = p.get_average_cost(results, True, episode_size)
                        casr, _ = p.get_average_success(results)
                    else:
                        cost, _ = p.get_average_cost_over_time(results, 1500, True)
                        cost = cost[0:1500]
                        casr, _ = p.get_average_success_over_time(results)
                        casr = casr[0:1500]

                    cost = np.insert(cost, 0, 10)
                    cost = cost * 10
                    cost_log = np.log10(cost + 1)
                    time_log = []
                    for k in range(len(cost_log)):
                        time_log.append(np.log10(k))
                    casr = np.insert(casr, 0, 0)
                    if len(casr) < 1500:
                        casr = np.pad(casr, ((0, 1500 - len(casr))), mode='constant',
                                      constant_values=np.mean(casr[len(casr) - 100:]))

                    for k in range(1, len(casr)):
                        casr[k] += casr[k - 1]

                    if tasks[t] == tasks[i * n_cols + j]:
                        axes[i, j].plot(time_log, cost_log, zorder=1, color=color_level_0, linestyle="dashed", label="Level-0-Transfer", linewidth=2)
                        asr_mean, asr_std = get_mean_over_window(np.diff(casr))
                        axes_casr[i, j].stairs(asr_mean, zorder=1, color=color_level_0, linestyle="dashed", label="Level-0-Transfer", linewidth=2)
                        #legend.append("Level-0-Transfer")#: " + tasks[t])
                        dcasr_set[i * n_cols + j].append(np.diff(casr))
                    else:
                        if general_objects:
                            cost_general_object.append(cost_log)
                            casr_general_object.append(casr)
                        else:
                            if tasks[t].split("_")[0] == "cylinder":
                                cost_cylinders.append(cost_log)
                                casr_cylinders.append(casr)
                            if tasks[t].split("_")[0] == "key":
                                cost_keys.append(cost_log)
                                casr_keys.append(casr)

                except (DataNotFoundError, DataError):
                    print("Cant find ",tags,"  i,j:",i,j)
                    pass
            print("cost cylinders: ",cost_cylinders,"  i,j:",i,j)
            mean_cost_cylinders = [0] * 1500
            mean_casr_cylinders = [0] * 1500
            mean_cost_keys = [0] * 1500
            mean_casr_keys = [0] * 1500
            mean_cost_general_object = [0] * 1500
            mean_casr_general_object = [0] * 1500
            std_cost_cylinders = [0] * 1500
            std_casr_cylinders = [0] * 1500
            std_cost_keys = [0] * 1500
            std_casr_keys = [0] * 1500
            std_cost_general_object = [0] * 1500
            std_casr_general_object = [0] * 1500

            if general_objects:
                for k in range(1500):
                    mean_cost = 0
                    mean_casr = 0
                    std_cost = 0
                    std_casr = 0
                    for m in range(len(cost_general_object)):
                        mean_cost += cost_general_object[m][k]
                        mean_casr += casr_general_object[m][k]
                    mean_cost_general_object[k] = mean_cost / len(cost_general_object)
                    mean_casr_general_object[k] = mean_casr / len(cost_general_object)
                    mean_dcasr_general_object = np.diff(mean_casr_general_object)
                    for m in range(len(cost_general_object)):
                        std_cost += np.power(cost_general_object[m][k] - mean_cost, 2)
                        std_casr += np.power(casr_general_object[m][k] - mean_casr, 2)

                    std_cost_general_object[k] = np.sqrt(std_cost / len(cost_general_object))
                    std_casr_general_object[k] = np.sqrt(std_casr / len(casr_general_object))
            else:
                for k in range(1500):
                    mean_cost = 0
                    mean_casr = 0
                    std_cost = 0
                    std_casr = 0
                    for m in range(len(cost_cylinders)):
                        mean_cost += cost_cylinders[m][k]
                        mean_casr += casr_cylinders[m][k]
                    mean_cost_cylinders[k] = mean_cost / len(cost_cylinders)
                    mean_casr_cylinders[k] = mean_casr / len(cost_cylinders)
                    mean_dcasr_cylinders = np.diff(mean_casr_cylinders)
                    for m in range(len(cost_keys)):
                        std_cost += np.power(cost_keys[m][k] - mean_cost, 2)
                        std_casr += np.power(casr_keys[m][k] - mean_casr, 2)

                    std_cost_cylinders[k] = np.sqrt(std_cost / len(cost_keys))  # should be len(cost_cylinders)
                    std_casr_cylinders = np.sqrt(std_casr / len(casr_keys))  # should be len(casr_cylinders)

                for k in range(1500):
                    mean_cost = 0
                    mean_casr = 0
                    std_cost = 0
                    std_casr = 0
                    for m in range(len(cost_keys)):
                        mean_cost += cost_keys[m][k]
                        mean_casr += casr_keys[m][k]
                    mean_cost_keys[k] = mean_cost / len(cost_keys)
                    mean_casr_keys[k] = mean_casr / len(cost_keys)
                    mean_dcasr_keys = np.diff(mean_casr_cylinders)
                    for m in range(len(cost_keys)):
                        std_cost += np.power(cost_keys[m][k] - mean_cost, 2)
                        std_casr += np.power(casr_keys[m][k] - mean_casr, 2)

                    std_cost_keys[k] = np.sqrt(std_cost / len(cost_keys))
                    std_casr_keys[k] = np.sqrt(std_casr / len(casr_keys))

            std_cost_cylinders = np.asarray(std_cost_cylinders)
            std_casr_cylinders = np.asarray(std_casr_cylinders)
            std_cost_keys = np.asarray(std_cost_keys)
            std_casr_keys = np.asarray(std_casr_keys)
            std_cost_general_object = np.asarray(std_cost_general_object)
            std_casr_general_object = np.asarray(std_casr_general_object)

            time_log = []
            for k in range(1500):
                time_log.append(np.log10(k))

            cylinder_asr_mean, cylinder_asr_std = get_mean_over_window(np.diff(mean_casr_cylinders))
            keys_asr_mean, keys_asr_std = get_mean_over_window(np.diff(mean_casr_keys))
            general_object_asr_mean, general_object_asr_std = get_mean_over_window(np.diff(mean_casr_general_object))

            if general_objects:
                dcasr_set[i * n_cols + j].append(mean_dcasr_general_object)
                dcasr_set[i * n_cols + j].append(mean_dcasr_general_object)
                #axes[i, j].plot(time_log, mean_cost_general_object, zorder=1, color=color_level_1, linestyle="dotted", label="Level-1-Transfer", linewidth=2)
                axes[i, j].plot(time_log, mean_cost_general_object, zorder=1, color=color_level_2, linestyle="dashdot", label="Level-2-Transfer", linewidth=2)
                #axes_casr[i, j].stairs(general_object_asr_mean, linestyle="dotted", zorder=1, color=color_level_1, label="Level-1-Transfer", linewidth=2)
                axes_casr[i, j].stairs(general_object_asr_mean, linestyle="dashdot", zorder=1, color=color_level_2, label="Level-2-Transfer", linewidth=2)
            else:
                if tasks[i * n_cols + j].split("_")[0] == "cylinder":
                    dcasr_set[i * n_cols + j].append(mean_dcasr_cylinders)
                    dcasr_set[i * n_cols + j].append(mean_dcasr_keys)
                    axes[i, j].plot(time_log, mean_cost_cylinders, zorder=1, color=color_level_1, linestyle="dotted", label="Level-1-Transfer", linewidth=2)
                    axes[i, j].plot(time_log, mean_cost_keys, zorder=1, color=color_level_2, linestyle="dashdot",  label="Level-2-Transfer", linewidth=2)
                    axes_casr[i, j].stairs(cylinder_asr_mean, linestyle="dotted", zorder=1, color=color_level_1, label="Level-1-Transfer", linewidth=2)
                    axes_casr[i, j].stairs(keys_asr_std, linestyle="dashdot", zorder=1, color=color_level_2, label="Level-2-Transfer", linewidth=2)
                else:
                    dcasr_set[i * n_cols + j].append(mean_dcasr_keys)
                    dcasr_set[i * n_cols + j].append(mean_dcasr_cylinders)
                    axes[i, j].plot(time_log, mean_cost_cylinders, zorder=1, color=color_level_2, linestyle="dotted",
                                    label="Level-2-Transfer")
                    axes[i, j].plot(time_log, mean_cost_keys, zorder=1, color=color_level_1, linestyle="dashdot",
                                    label="Level-1-Transfer")
                    axes_casr[i, j].stairs(keys_asr_mean, linestyle="dashdot", zorder=1, color=color_level_1, label="Level-1-Transfer", linewidth=2)
                    axes_casr[i, j].stairs(cylinder_asr_mean, linestyle="dotted", zorder=1, color=color_level_2, label="Level-2-Transfer", linewidth=2)

            if i == 0 and j == 0:
                current_handles, current_labels = axes[i, j].get_legend_handles_labels()
                new_lables = [label for label in current_labels]
                #new_lables = [current_labels[1], current_labels[2], current_labels[3], current_labels[0]]
                new_handles = [handle for handle in current_handles]
                #new_handles = [current_handles[1], current_handles[2], current_handles[3], current_handles[0]]
                axes[i, j].legend(new_handles, new_lables, fontsize=16, loc="center left", bbox_to_anchor=(0, 1.15), ncol=4)
                axes_casr[i, j].legend(new_handles, new_lables, fontsize=16, loc='center left', bbox_to_anchor=(0, 1.15), ncol=4)

            # if i == 0:
            #     pass
            #     axes[i, j].annotate("t" + str(j), xy=(0.5, 1), xytext=(0, 5),
            #                         xycoords='axes fraction', textcoords='offset points',
            #                         size='large', ha='center', va='baseline')
            if j == 0:
                ticks = [0.2, 0.4, 0.6, 0.8, 1, 1.2]
                axes[i, j].set_yticks(ticks)
                axes[i, j].set_yticklabels(list(map(str, ticks)))
                ticks = [0.2, 0.4, 0.6, 0.8, 1]
                axes_casr[i, j].set_yticks(ticks)
                axes_casr[i, j].set_yticklabels(list(map(str, ticks)))
            #     pass
            #     axes[i, j].annotate("t" + str(i), xy=(0, 0.5), xytext=(-axes[i, j].yaxis.labelpad - 5, 0),
            #                         xycoords=axes[i, j].yaxis.label, textcoords='offset points',
            #                         size='large', ha='right', va='center')
            #     axes[i, j].set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1])
            #     axes[i, j].set_yticklabels([''] * 6)
            if i == n_rows - 1:
                if trial_wise is True:
                    if episode_wise is True:
                        axes[i, j].set_xticks([2, 4, 6, 8, 10])
                        axes[i, j].set_xticklabels(["2", "4", "6", "8", "10"])
                    else:
                        axes[i, j].set_xticks([25, 50, 75, 100, 130])
                        axes[i, j].set_xticklabels(["25", "50", "75", "100", "130"])
                        axes_casr[i, j].set_xticks([25, 50, 75, 100, 130])
                        axes_casr[i, j].set_xticklabels(["25", "50", "75", "100", "130"])
                else:
                    ticks = [1.5, 2.0, 2.5, 3]
                    axes[i, j].set_xticks(ticks)
                    axes[i, j].set_xticklabels(list(map(str, ticks)))
                    ticks = [1, 2, 3, 4, 5, 6, 7]
                    axes_casr[i, j].set_xticks(ticks)
                    #axes_casr[i, j].set_xticks([250, 500, 750, 1000, 1250, 1500])
                    axes_casr[i, j].set_xticklabels(["200", "400", "600", "800", "1000", "1200", "1400"])
            axes[i, j].tick_params(axis='both', which='major', labelsize=12)
            axes_casr[i, j].tick_params(axis='both', which='major', labelsize=12)

    x_tasks = np.arange(9) + 1
    axes_dcasr.bar(x_tasks - 0.3, 1, width=0.2, label="None-Transfer")
    axes_dcasr.bar(x_tasks - 0.1, 1, width=0.2, label="Level-0-Transfer")
    axes_dcasr.bar(x_tasks + 0.1, 1, width=0.2, label="Level-1-Transfer")
    axes_dcasr.bar(x_tasks + 0.3, 1, width=0.2, label="Level-2-Transfer")
    ticks = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    axes_dcasr.set_xticks(ticks)
    axes_dcasr.set_xticklabels(["t_1", "t_2", "t_3", "t_4", "t_5", "t_6", "t_7", "t_8", "t_9"])

    ax = fig.add_subplot(111, frame_on=False)
    ax_casr = fig_casr.add_subplot(111, frame_on=False)
    ax.tick_params(labelcolor="none", bottom=False, left=False)
    ax_casr.tick_params(labelcolor="none", bottom=False, left=False)
    if trial_wise is True:
        if episode_wise is True:
            ax.xlabel("Episode [1]")
            ax_casr.xlabel("Episode [1]")
        else:
            ax.set_xlabel("Trial [1]")
            ax_casr.set_xlabel("Trial [1]")
    else:
        ax.set_xlabel(r"Learning Time [$\text{log}_{10}$(s)]", fontsize=16)
        ax_casr.set_xlabel(r"Learning Time [s]", fontsize=16)
    ax.set_ylabel(r"Execution Time [$\text{log}_{10}$(s)]", fontsize=16)
    ax_casr.set_ylabel(r"ALSR [1]", fontsize=16)
    ax_casr.yaxis.set_label_coords(-0.05, 0.5)

    fig.set_size_inches(16, 9)
    fig_casr.set_size_inches(16, 9)
    fig.savefig("results_cost_new.png", bbox_inches='tight', dpi=300)
    fig_casr.savefig("results_calsc_new.png", bbox_inches='tight', dpi=300)

    plt.show()


def plot_ler_matrix2():

    plt.rcParams.update({
        "text.usetex": True,
        'text.latex.preamble': [r'\usepackage{amssymb}',r'\usepackage{amsmath}',r'\usepackage{mathbbol}'],
        "font.family": 'serif',
        "font.size": 16
    })

    # opening the CSV file
    data_ler = []
    data_es = []
    data_speedup = []

    with open('ler_matrix.csv', mode='r') as file:
        # reading the CSV file
        csvFile = csv.reader(file)

        # displaying the contents of the CSV file
        for lines in csvFile:
            tmp = []
            try:
                for i in range(1, len(lines)):
                    tmp.append(float(lines[i]))
            except ValueError:
                continue
            data_ler.append(tmp)

    with open('es_matrix.csv', mode='r') as file:
        # reading the CSV file
        csvFile = csv.reader(file)

        # displaying the contents of the CSV file
        for lines in csvFile:
            tmp = []
            try:
                for i in range(1, len(lines)):
                    tmp.append(float(lines[i]))
            except ValueError:
                continue
            data_es.append(tmp)

    with open('speedup_matrix.csv', mode='r') as file:
        # reading the CSV file
        csvFile = csv.reader(file)

        # displaying the contents of the CSV file
        for lines in csvFile:
            tmp = []
            try:
                for i in range(1, len(lines)):
                    tmp.append(float(lines[i]))
            except ValueError:
                continue
            data_speedup.append(tmp)

    x = np.linspace(1, 9, 9)
    y = np.linspace(1, 9, 9)
    Z_ler = np.zeros((len(x), len(y)))
    Z_es = np.zeros((len(x), len(y)))
    Z_speedup = np.zeros((len(x), len(y)))

    for i in range(len(x)):
        for j in range(len(y)):
            Z_ler[i, j] = data_ler[i][j]
            Z_es[i, j] = data_es[i][j]
            Z_speedup[i, j] = np.log10(data_speedup[i][j])

    Z_ler = Z_ler.transpose()
    Z_es = Z_es.transpose()
    Z_speedup = Z_speedup.transpose()

    fig, axes = plt.subplots(1, 3, sharex=True, sharey=True, gridspec_kw={'hspace': 0.2, 'wspace': 0.2})
    fig_legend, axes_legend = plt.subplots()
    colormap = "Oranges"
    Zs = [Z_es, Z_speedup, Z_ler]
    i = 0
    for ax in axes:
        im = ax.imshow(Zs[i], cmap=colormap)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.05)
        fig.colorbar(im, cax=cax, orientation='vertical')
        i += 1

    # im1 = axes[0, 0].imshow(Z_ler, cmap=colormap)
    # divider = make_axes_locatable(axes[0, 0])
    # cax = divider.append_axes('right', size='5%', pad=0.05)
    # fig.colorbar(im1, cax=cax, orientation='vertical')
    #
    # im2 = axes[0, 1].imshow(Z_es, cmap=colormap)
    # divider = make_axes_locatable(axes[0, 1])
    # cax = divider.append_axes('right', size='5%', pad=0.05)
    # fig.colorbar(im2, cax=cax, orientation='vertical')
    #
    # im3 = axes[1, 0].imshow(Z_speedup, cmap=colormap)
    # divider = make_axes_locatable(axes[1, 0])
    # cax = divider.append_axes('right', size='5%', pad=0.05)
    # fig.colorbar(im3, cax=cax, orientation='vertical')

    ler_level_0 = []
    ler_level_1 = []
    ler_level_2 = []

    et_level_0 = []
    et_level_1 = []
    et_level_2 = []

    speedup_level_0 = []
    speedup_level_1 = []
    speedup_level_2 = []

    data_legend = np.zeros((9, 9))

    for i in range(9):
        for j in range(9):
            if i == j:
                ler_level_0.append(Z_ler[i, j])
                et_level_0.append(Z_es[i, j])
                speedup_level_0.append(Z_speedup[i, j])
                data_legend[i, j] = 1
            elif i < 6 and j < 6:
                ler_level_1.append(Z_ler[i, j])
                et_level_1.append(Z_es[i, j])
                speedup_level_1.append(Z_speedup[i, j])
                data_legend[i, j] = 0.5
            elif i >= 6 and j >= 6:
                ler_level_1.append(Z_ler[i, j])
                et_level_1.append(Z_es[i, j])
                speedup_level_1.append(Z_speedup[i, j])
                data_legend[i, j] = 0.5
            else:
                ler_level_2.append(Z_ler[i, j])
                et_level_2.append(Z_es[i, j])
                speedup_level_2.append(Z_speedup[i, j])
                data_legend[i, j] = 0

    im = axes_legend.imshow(data_legend, cmap="binary")
    # divider = make_axes_locatable(axes[1, 1])
    # cax = divider.append_axes('right', size='5%', pad=0.05)
    # fig.colorbar(im4, cax=cax, orientation='vertical')

    mean_ler_level_0 = np.mean(ler_level_0)
    mean_ler_level_1 = np.mean(ler_level_1)
    mean_ler_level_2 = np.mean(ler_level_2)

    mean_et_level_0 = np.mean(et_level_0)
    mean_et_level_1 = np.mean(et_level_1)
    mean_et_level_2 = np.mean(et_level_2)

    mean_speedup_level_0 = np.mean(speedup_level_0)
    mean_speedup_level_1 = np.mean(speedup_level_1)
    mean_speedup_level_2 = np.mean(speedup_level_2)

    std_ler_level_0 = np.std(ler_level_0)
    std_ler_level_1 = np.std(ler_level_1)
    std_ler_level_2 = np.std(ler_level_2)

    std_et_level_0 = np.std(et_level_0)
    std_et_level_1 = np.std(et_level_1)
    std_et_level_2 = np.std(et_level_2)

    std_speedup_level_0 = np.std(speedup_level_0)
    std_speedup_level_1 = np.std(speedup_level_1)
    std_speedup_level_2 = np.std(speedup_level_2)

    print("MEAN: 0-LER: " + str(mean_ler_level_0) + ", 1-LER: " + str(mean_ler_level_1) + ", 2-LER:" + str(mean_ler_level_2))
    print("STD: 0-LER: " + str(std_ler_level_0) + ", 1-LER: " + str(std_ler_level_1) + ", 2-LER:" + str(std_ler_level_2))

    print("MEAN: 0-ET: " + str(mean_et_level_0) + ", 1-ET: " + str(mean_et_level_1) + ", 2-ET:" + str(
        mean_et_level_2))
    print(
        "STD: 0-ET: " + str(std_et_level_0) + ", 1-ET: " + str(std_et_level_1) + ", 2-ET:" + str(std_et_level_2))

    print("MEAN: 0-SPEEDUP: " + str(mean_speedup_level_0) + ", 1-SPEEDUP: " + str(mean_speedup_level_1) + ", 2-SPEEDUP:" + str(
        mean_speedup_level_2))
    print(
        "STD: 0-SPEEDUP: " + str(std_speedup_level_0) + ", 1-SPEEDUP: " + str(std_speedup_level_1) + ", 2-SPEEDUP:" + str(std_speedup_level_2))

    for ax in axes.reshape(-1):
        ax.plot([-0.5, 8.5], [5.5, 5.5], color="white", linewidth=4)
        ax.plot([5.5, 5.5], [-0.5, 8.5], color="white", linewidth=4)
        # axes[i].text(0, 3, "Level-1-Transfers", ha='left', rotation=0, wrap=True, fontsize=16, color="gray")
        # axes[i].text(7, 4.5, "Level-2-Transfers", ha='left', rotation=90, wrap=True, fontsize=16, color="gray")
        # axes[i].text(0, 7, "Level-2-Transfers", ha='left', rotation=0, wrap=True, fontsize=16, color="gray")

        ax.set_xticks(x-1)
        ax.set_xticklabels(["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9"], fontsize=16)

    axes[0].set_yticks(y-1)
    axes[0].set_yticklabels(["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9"], fontsize=16)

    axes[0].set_title("Empirical Transferability (ET)", fontsize=16)
    axes[1].set_title("Speedup Factor (log base 10)", fontsize=16)
    axes[2].set_title("Learning Effort Ratio (LER)", fontsize=16)

    white_patch = mpatches.Patch(color='white', label='Level-2-Transfer')
    gray_patch = mpatches.Patch(color='gray', label='Level-1-Transfer')
    black_patch = mpatches.Patch(color='black', label='Level-0-Transfer')
    # axes_legend.legend(handles=[black_patch, gray_patch, white_patch], bbox_to_anchor=(1.2, 1.1), ncol=3)
    axes_legend.set_xticks(x-1)
    axes_legend.set_xticklabels(["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9"], fontsize=16)
    axes_legend.set_yticks(y-1)
    axes_legend.set_yticklabels(["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9"], fontsize=16)

    fig.set_size_inches(16, 9)
    fig.savefig("results_matrices.png", bbox_inches='tight', dpi=300)
    fig_legend.set_size_inches(16, 9)
    fig_legend.savefig("results_matrices_legend.png", bbox_inches='tight', dpi=300)

    X = np.arange(3)+1
    fig_means, axes_means = plt.subplots(1, 1, sharex=True, sharey=True, gridspec_kw={'hspace': 0.2, 'wspace': 0.1})
    axes_means.bar(X-0.25, [mean_et_level_0, mean_speedup_level_0, mean_ler_level_0], label="Level-0-Transfer", color=color_level_0, width=0.25, hatch="\\\\//")
    axes_means.bar(X, [mean_et_level_1, mean_speedup_level_1, mean_ler_level_1], label="Level-1-Transfer", color=color_level_1, width=0.25, hatch="//")
    axes_means.bar(X+0.25, [mean_et_level_2, mean_speedup_level_2, mean_ler_level_2], label="Level-2-Transfer", color=color_level_2, width=0.25, hatch="\\\\")
    axes_means.legend(bbox_to_anchor=(1.1, 1.17), ncol=3)
    axes_means.set_ylabel("Mean")
    axes_means.set_xticks([1, 2, 3])
    axes_means.set_xticklabels(["ET", "Speedup Factor (log base 10)", "LER"])
    fig_means.set_size_inches(8, 4.5)
    fig_means.savefig("results_means.png", bbox_inches='tight', dpi=300)

    plt.show()


def test_speedup(base_task: str, second_task: str):
    trial_wise = False
    episode_size = 1
    p = DataProcessor()

    tags = ["transfer_learning", base_task]
    results = get_multiple_experiment_data("collective-control-001.local", "insert_object",
                                           results_db="transfer_base_v2",
                                           filter={"meta.tags": {"$all": tags}})
    if trial_wise is True:
        base_cost, _ = p.get_average_cost(results, True, episode_size)
        base_casr, _ = p.get_average_success(results)
    else:
        base_cost, _ = p.get_average_cost_over_time(results, 1500, True)
        base_cost = base_cost[0:1500]
        base_casr, _ = p.get_average_success_over_time(results)
        base_casr = base_casr[0:1500]
    base_cost = np.insert(base_cost, 0, 10)
    base_cost = base_cost * 10

    tags = ["transfer_learning", base_task, "from_" + second_task]
    results = get_multiple_experiment_data("collective-control-001.local", "insert_object",
                                           results_db="transfer_all_v2",
                                           filter={"meta.tags": {"$all": tags}})
    if trial_wise is True:
        cost, _ = p.get_average_cost(results, True, episode_size)
        casr, _ = p.get_average_success(results)
    else:
        cost, _ = p.get_average_cost_over_time(results, 1500, True)
        cost = cost[0:1500]
        casr, _ = p.get_average_success_over_time(results)
        casr = casr[0:1500]
    cost = np.insert(cost, 0, 10)
    cost = cost * 10

    speedup = calculate_speedup(base_cost, cost)
    print(speedup)


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


def calculate_speedup(base_cost: list, cost: list):
    confidences = np.linspace(0.02, 0.1, 8)
    speedup_sum = 0
    for c in confidences:
        index_thr_base_cost = find_convergence(base_cost, c)
        thr_base_cost = base_cost[index_thr_base_cost]
        index_thr_transfer_cost = np.where(cost < thr_base_cost + c)
        if index_thr_transfer_cost[0].size == 0:
            index_thr_transfer_cost = 1
            index_thr_base_cost = 1
        else:
            index_thr_transfer_cost = index_thr_transfer_cost[0][0]
        speedup_sum += index_thr_base_cost / index_thr_transfer_cost

    return speedup_sum / len(confidences)


def calculate_kl_divence(base_cost: list, cost: list):
    kl = 0
    for i in range(len(base_cost)):
        kl += base_cost[i] * np.log(base_cost[i] / cost[i])

    return kl


def count_transfer_learning(host: str, db: str, task_type: str):
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", "key_abus_e30",
             "key_pad", "key_old", "key_hatch"]
    client = MongoDBClient(host)
    for t1 in tasks:
        for t2 in tasks:
            docs = client.read(db, task_type, {"meta.tags": {"$all": ["transfer_learning", t1, "from_" + t2]}})
            if len(docs) != 10:
                print("Experiment with tags [" + t1 + ", " + t2 + "] has " + str(len(docs)) + " documents.")


def cm2inch(value):
    return value / 2.54


def plot_ler_matrix():
    ler_matrix_csv = open('ler_matrix.csv', 'r')
    plots = csv.reader(ler_matrix_csv, delimiter=',')
    ler_matrx = np.zeros((9, 9))
    ler_matrix_sorted = np.zeros((9, 9))
    ler_matrix_tasks = np.zeros((9, 9))
    # bar_colors = ["blue", "red", "green", "yellow", "orange", "cyan", "pink", "saddlebrown", "lavender"]
    bar_colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", "key_pad",
             "key_old", "key_hatch"]
    tasks_short = ["$t_1$", "$t_2$", "$t_3$", "$t_4$", "$t_5$", "$t_6$", "$t_7$", "$t_8$", "$t_9$"]
    cnt_row = 0

    for row in plots:
        if cnt_row == 0:
            cnt_row += 1
            continue
        for i in range(len(row)):
            if i == 0:
                continue
            ler_matrx[cnt_row - 1, i - 1] = float(row[i])
        ler_matrix_sorted[cnt_row - 1] = np.sort(ler_matrx[cnt_row - 1])
        ler_matrix_tasks[cnt_row - 1] = np.argsort(ler_matrx[cnt_row - 1])
        cnt_row += 1
    # single axes
    fig, ax = plt.subplots(num="fig_ler")
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    bar_width = 0.6  # standard
    dimw = bar_width / len(tasks)
    x = np.arange(len(tasks))
    for col in range(len(tasks)):
        colors = [bar_colors[int(j)] for j in ler_matrix_tasks[:, col]]
        y = [data for data in ler_matrix_sorted[:, col]]
        legend = [data for data in ler_matrix_tasks[:, col]]
        for row in range(len(tasks)):
            if row == 0:
                legend = tasks[int(ler_matrix_tasks[row, col])]
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color=colors[row], label=legend)
            else:
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color=colors[row])
    handles, labels = ax.get_legend_handles_labels()
    _, labels, handles = zip(*sorted(zip(ler_matrix_tasks[0, :], labels, handles), key=lambda t: t[0]))
    fig.set_size_inches(cm2inch(30), cm2inch(10))
    fontsize = 12
    ax.set_xticks(x + len(tasks) * dimw / 2)
    ax.set_xticklabels(tasks, fontsize=fontsize)
    ax.set_ylim(0, 2.1)
    ax.set_yticks([0, 0.4, 0.8, 1.2, 1.6, 2])
    ax.grid(axis="y")
    ax.set_ylabel("LER [1]", fontsize=fontsize)
    ax.tick_params(labelsize=fontsize)
    legend = ax.legend(handles, labels, loc="upper left", title="knowledge sources", fontsize=fontsize - 2)
    plt.setp(legend.get_title(), fontsize=fontsize - 2)
    plt.tight_layout()
    fig.savefig('fig_ler.png', bbox_inches='tight', dpi=500)
    plt.show(block=True)


def plot_es_matrix():
    ler_matrix_csv = open('es_matrix.csv', 'r')
    plots = csv.reader(ler_matrix_csv, delimiter=',')
    ler_matrx = np.zeros((9, 9))
    ler_matrix_sorted = np.zeros((9, 9))
    ler_matrix_tasks = np.zeros((9, 9))
    bar_colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60",
             "key_pad", "key_old", "key_hatch"]
    cnt_row = 0
    for row in plots:
        if cnt_row == 0:
            cnt_row += 1
            continue
        for i in range(len(row)):
            if i == 0:
                continue
            ler_matrx[cnt_row - 1, i - 1] = float(row[i])
        ler_matrix_sorted[cnt_row - 1] = np.sort(ler_matrx[cnt_row - 1])
        ler_matrix_tasks[cnt_row - 1] = np.argsort(ler_matrx[cnt_row - 1])
        cnt_row += 1

    # single axes
    fig, ax = plt.subplots(num="fig_es")
    bar_width = 0.6  # standard
    dimw = bar_width / len(tasks)
    x = np.arange(len(tasks))
    for col in range(len(tasks)):
        colors = [bar_colors[int(j)] for j in ler_matrix_tasks[:, col]]
        y = [data for data in ler_matrix_sorted[:, col]]
        legend = [data for data in ler_matrix_tasks[:, col]]
        for row in range(len(tasks)):
            if row == 0:
                legend = tasks[int(ler_matrix_tasks[row, col])]
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color=colors[row], label=legend)
            else:
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color=colors[row])
    handles, labels = ax.get_legend_handles_labels()
    _, labels, handles = zip(*sorted(zip(ler_matrix_tasks[0, :], labels, handles), key=lambda t: t[0]))
    fig.set_size_inches(cm2inch(30), cm2inch(10))
    fontsize = 12
    ax.set_xticks(x + len(tasks) * dimw / 2)
    ax.set_xticklabels(tasks, fontsize=fontsize)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    ax.set_ylim(0, 1.02)
    ax.grid(axis="y")
    ax.set_ylabel("ES []", fontsize=fontsize)
    legend = ax.legend(handles, labels, loc="upper left", title="knowledge sources", fontsize=fontsize - 2)
    plt.setp(legend.get_title(), fontsize=fontsize - 2)
    plt.tight_layout()
    fig.savefig('fig_es.png', dpi=500)
    plt.show()


def plot_speedup_matrix():
    ler_matrix_csv = open('speedup_matrix.csv', 'r')
    plots = csv.reader(ler_matrix_csv, delimiter=',')
    ler_matrx = np.zeros((9, 9))
    ler_matrix_sorted = np.zeros((9, 9))
    ler_matrix_tasks = np.zeros((9, 9))
    bar_colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60",
             "key_pad", "key_old", "key_hatch"]
    cnt_row = 0
    for row in plots:
        if cnt_row == 0:
            cnt_row += 1
            continue
        for i in range(len(row)):
            if i == 0:
                continue
            ler_matrx[cnt_row - 1, i - 1] = float(row[i])
        ler_matrix_sorted[cnt_row - 1] = np.sort(ler_matrx[cnt_row - 1])
        ler_matrix_tasks[cnt_row - 1] = np.argsort(ler_matrx[cnt_row - 1])
        cnt_row += 1

    # single axes
    fig, ax = plt.subplots(num="fig_speedup")
    bar_width = 0.6  # standard
    dimw = bar_width / len(tasks)
    x = np.arange(len(tasks))
    for col in range(len(tasks)):
        colors = [bar_colors[int(j)] for j in ler_matrix_tasks[:, col]]
        y = [data for data in ler_matrix_sorted[:, col]]
        legend = [data for data in ler_matrix_tasks[:, col]]
        for row in range(len(tasks)):
            if row == 0:
                legend = tasks[int(ler_matrix_tasks[row, col])]
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color=colors[row], label=legend)
            else:
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color=colors[row])
    handles, labels = ax.get_legend_handles_labels()
    _, labels, handles = zip(*sorted(zip(ler_matrix_tasks[0, :], labels, handles), key=lambda t: t[0]))
    fig.set_size_inches(cm2inch(30), cm2inch(10))
    fontsize = 12
    ax.set_xticks(x + len(tasks) * dimw / 2)
    ax.set_xticklabels(tasks, fontsize=fontsize)
    ax.set_yscale('log')
    ax.grid(axis="y")
    ax.set_ylabel("speedup [s]", fontsize=fontsize)
    ax.tick_params(labelsize=fontsize)
    legend = ax.legend(handles, labels, loc="upper right", title="knowledge sources", fontsize=fontsize - 2)
    plt.setp(legend.get_title(), fontsize=fontsize - 2)
    plt.tight_layout()
    fig.savefig('fig_speedup.png', dpi=500)
    plt.show()


def transfer_learning_benchmark():
    p = DataProcessor()
    plot = Plotter()
    tags = ["transfer_learning", "shift_0"]
    results = get_multiple_experiment_data("localhost", "benchmark_rastrigin",
                                           results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost(results, True, 6)
    cost = np.insert(cost, 0, 1)
    plt.plot(cost)

    tags = ["transfer_learning", "shift_1", "from_shift_0"]
    results = get_multiple_experiment_data("localhost", "benchmark_rastrigin",
                                           results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost(results, True, 6)
    cost = np.insert(cost, 0, 1)
    plt.plot(cost)
    plt.show()


def transfer_learning_test():
    p = DataProcessor()
    plot = Plotter()
    tags = ["transfer_learning_test", "cylinder_40"]
    results = get_multiple_experiment_data("collective-panda-001.local", "insert_object",
                                           results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost(results, True, 12)
    cost = np.insert(cost, 0, 1)
    plt.plot(cost)

    tags = ["transfer_learning_test", "cylinder_40", "from_cylinder_20"]
    results = get_multiple_experiment_data("collective-panda-001.local", "insert_object",
                                           results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost(results, True, 12)
    cost = np.insert(cost, 0, 1)
    plt.plot(cost)
    plt.show()


def knowledge_quality(tags, hosts=["localhost"], legend=None):
    filter = {"meta.tags": tags}
    knowledge_mode = "global"
    # task_type = "insert_object"
    task_type = "benchmark_rastrigin"

    p = DataProcessor()

    results = []
    for host in hosts:
        results.extend(get_multiple_experiment_data(host, task_type, knowledge_mode, filter=filter))
    results = p.sort_over_time(results)

    print("number of results: ", len(results))

    distances = []
    for r in results:
        lowest_cost = r.get_lowest_cost()
        init_knowledge = r.knowledge
        if init_knowledge is None:
            init_knowledge = r.get_theta_per_trial()[0]  # take first trial if no initial knowledge available
        init_knowledge = p.dict_to_list(init_knowledge)
        best_theta = p.dict_to_list(r.get_best_theta())
        created_knowledge = get_multiple_knowledge_data(hosts[0], task_type, knowledge_mode,
                                                        {"meta.knowledge_source": r.uuid, "meta.tags": tags})[0]
        created_theta = created_knowledge.get_theta()

        dist = np.linalg.norm(np.array(created_theta) - np.array(init_knowledge))
        distances.append(dist)
    plot.plot_knowledge_error(distances, legend)


def transfer_learning_parameters(filter, host, result_db="transfer_all_v2"):
    # calculate the mean distance between optimas and their initial knowledges
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", "key_pad",
             "key_old", "key_hatch"]  # ,"key_abus_e30", "key_pad", "key_old", "key_hatch"]
    p = DataProcessor()
    from knowledge_processor.knowledge_manager import KnowledgeManager
    from mongodb_client.mongodb_client import MongoDBClient
    manager = KnowledgeManager(host)
    client = MongoDBClient(host)
    data = {}
    for task in tasks:
        data[task] = {}
        for i in range(len(tasks)):
            print("\n", task, "   from_", tasks[i])
            try:
                tags = ["transfer_learning", task, "from_" + tasks[i]]
                results = get_multiple_experiment_data(host, "insert_object",
                                                       results_db=result_db,
                                                       filter={"meta.tags": tags})
            except (DataNotFoundError, DataError):
                print("No data found for experiment (" + str(i) + ")")
                continue
            distances = []
            for r in results:
                task_identity = {
                    "task_type": r.meta_data["task_type"],
                    "optimum_weights": r.meta_data["cost_function"]["optimum_weights"],
                    "geometry_factor": r.meta_data["cost_function"]["geometry_factor"],
                    "tags": r.tags
                }
                optimum = manager.get_knowledge_by_identity(client, task_identity, result_db, None)
                optimum = r.normalize_result(optimum["parameters"])
                init_knowledge = r.get_knowledge_norm()
                # optimum = r.get_best_theta_norm()
                if init_knowledge is None:
                    continue
                dist = np.linalg.norm(np.array(p.dict_to_list(init_knowledge)) - np.array(p.dict_to_list(optimum)))
                distances.append(dist)
                print(r.tags)
            mean_dist = np.mean(distances)
            std_dist = np.std(distances)
            data[task]["from_" + tasks[i]] = {"mean_dist": mean_dist, "std_dist": std_dist}
    import pprint
    pprint.pprint(data)
    plot.plot_parameter_similarity(data)
    header = np.array(tasks)

    # save mean distance as csv matrix:
    means_mtx = []
    stds_mtx = []
    for task_key in data.keys():
        task_means = []
        task_stds = []
        for knowledge_key in data[task_key].keys():
            task_means.append(data[task_key][knowledge_key]["mean_dist"])
            task_stds.append(data[task_key][knowledge_key]["mean_dist"])
        means_mtx.append(task_means)
        stds_mtx.append(task_stds)
    means_mtx = np.array(means_mtx)
    means_mtx = np.transpose(means_mtx)

    stds_mtx = np.array(stds_mtx)
    means_mtx = means_mtx.astype('|S4')
    stds_mtx = stds_mtx.astype('|S4')
    means_mtx = np.vstack((header, means_mtx))
    stds_mtx = np.vstack((header, stds_mtx))

    header = np.array(["from_" + task for task in header])
    header = np.insert(header, 0, "")

    means_mtx = np.hstack((header.reshape(-1, 1), means_mtx))
    stds_mtx = np.hstack((header.reshape(-1, 1), stds_mtx))

    np.savetxt("optima_knowledge_distance_mean.csv", means_mtx, delimiter=",", fmt="%s")
    np.savetxt("optima_knowledge_distance_std.csv", stds_mtx, delimiter=",", fmt="%s")


def no_transfer_learning_parameters(filter, host):
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50",
             "cylinder_60"]  # ,"key_abus_e30", "key_pad", "key_old", "key_hatch"]
    p = DataProcessor()
    data = {}
    for task in tasks:
        data[task] = {}
        try:
            tags = ["transfer_learning", task]
            results = get_multiple_experiment_data(host, "insert_object",
                                                   results_db="results_tl_base",
                                                   filter={"meta.tags": tags})
        except (DataNotFoundError, DataError):
            print("No data found for experiment (" + str(i) + ")")
            continue
        distances = []
        for r in results:
            init_knowledge = r.get_default_centroid()
            optimum = r.get_best_theta_norm()
            if init_knowledge is None:
                continue
            dist = np.linalg.norm(np.array(p.dict_to_list(init_knowledge)) - np.array(p.dict_to_list(optimum)))
            distances.append(dist)
            print(r.tags)
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        data[task]["default centroid"] = {"mean_dist": mean_dist, "std_dist": std_dist}
    plot.plot_default_centroid_dist(data)


def optima_distances(filter, host, results_db):
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50",
             "cylinder_60"]  # ,"key_abus_e30", "key_pad", "key_old", "key_hatch"]
    p = DataProcessor()
    from knowledge_processor.knowledge_manager import KnowledgeManager
    from mongodb_client.mongodb_client import MongoDBClient
    manager = KnowledgeManager(host)
    client = MongoDBClient(host)
    data = {}
    for task in tasks:
        data[task] = {}
        try:
            tags = ["transfer_learning_test", task]
            results = get_multiple_experiment_data(host, "insert_object",
                                                   results_db=results_db,
                                                   filter={"meta.tags": tags})
        except (DataNotFoundError, DataError):
            print("No data found for experiment (" + str(task) + ")")
            continue
        distances = []
        optima = []
        for r in results:
            if r.meta_data["init_knowledge"]["content"]:
                continue
            task_identity = {
                "task_type": r.meta_data["task_type"],
                "optimum_weights": r.meta_data["cost_function"]["optimum_weights"],
                "geometry_factor": r.meta_data["cost_function"]["geometry_factor"],
                "tags": r.tags
            }
            optimum = manager.get_knowledge_by_identity(client, task_identity, results_db, None)
            optimum = r.normalize_result(optimum["parameters"])
            optimum = p.dict_to_list(r.get_best_theta_norm())
            optima.append(optimum)
        optima_matrix = []
        for optimum_a in optima:
            dinstances = []
            for optimum_b in optima:
                dist = np.linalg.norm(np.array(optimum_a) - np.array(optimum_b))
                dinstances.append(dist)
            optima_matrix.append(dinstances)
        print(task, " mean_distance: ", np.mean(optima_matrix))
        plot.plot_table(optima_matrix, task)


def print_cost_grid():
    results = get_multiple_experiment_data("collective-panda-002.local", "insert_object", "global_ml_results",
                                           {"meta.tags": {"$all": ["collective_learning_insertion_screen_001"]}})
    processor = DataProcessor()
    raw_data = processor.get_optima_by_task_identity(results, 0.05)

    z = raw_data[:, -1]

    x = np.array([0.1, 0.3, 0.5, 0.8, 1])
    y = np.linspace(0, 1, 11)
    z = np.zeros((len(x), len(y)))

    for i in range(len(x)):
        for j in range(len(y)):
            for k in range(len(raw_data)):
                if isclose(x[i], raw_data[k, 0]) and isclose(y[j], raw_data[k, 1]):
                    z[i, j] = raw_data[k, -1]

    x, y = np.meshgrid(x, y)
    print(x)
    print(y)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(x, y, np.transpose(z))
    plt.xlabel("geometry")
    plt.ylabel("cost")
    plt.show()


def color_matrix(name="es_matrix.csv"):
    from matplotlib import cm
    from matplotlib.colors import ListedColormap, LinearSegmentedColormap

    data = np.genfromtxt(name, delimiter=',')
    data = np.delete(data, 0, 0)  # deleting names
    data = np.delete(data, 0, 1)
    min_value = min(data.flatten())
    max_value = max(data.flatten())
    cmap = cm.get_cmap('turbo', (max_value - min_value) * 100)
    print(data)
    print(min_value)
    print(max_value)
    fig, ax = plt.subplots(1, 1, constrained_layout=True)
    psm = ax.pcolormesh(data, cmap=cmap, rasterized=True, vmin=min_value, vmax=max_value)
    ax.set_title(name[:-4])
    ax.set_xlabel("task learned")
    ax.set_ylabel("knowledge from task")
    fig.colorbar(psm, ax=ax)
    plt.show()


def plot_collective_benchmark():
    host = "collective-panda-002.local"
    tags = ["collective_learning_benchmark_single2_5_ind"]
    p = DataProcessor()

    print("Plotting single_ind_5")
    results = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    # cost = p.get_average_cost_over_time(results, 1500, True)
    cost = p.get_average_cost(results, True, 5)
    plt.plot(cost)

    tags = ["collective_learning_benchmark_single2_10_ind"]
    print("Plotting single_ind_10")
    results = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    # cost = p.get_average_cost_over_time(results, 1500, True)
    cost = p.get_average_cost(results, True, 10)
    plt.plot(cost)

    tags = ["collective_learning_benchmark_share2_5_ind", "collective-panda-002.local"]
    print("Plotting share_ind_5")
    results = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    # cost = p.get_average_cost_over_time(results, 1500, True)
    cost = p.get_average_cost(results, True, 5)
    plt.plot(cost)

    tags = ["collective_learning_benchmark_share2_10_ind", "collective-panda-002.local"]
    print("Plotting share_ind_10")
    results = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    # cost = p.get_average_cost_over_time(results, 1500, True)
    cost = p.get_average_cost(results, True, 5)
    plt.plot(cost)

    plt.legend(("Single_5", "Single_10", "Shared_10", "Shared_15"))

    plt.ylim([0, 1])
    plt.show()


def plot_difference_curve():
    host = "collective-panda-002.local"
    results1 = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results",
                                            filter={"meta.tags": {"$all": ["collective_learning_benchmark_single_t0"]}})
    results2 = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results",
                                            filter={"meta.tags": {"$all": ["collective_learning_benchmark_share_t"]}})
    p = DataProcessor()
    p.get_cost_difference_curve(results1, results2)


def plot_collective_benchmark_2():
    host = "collective-panda-002.local"
    tags = [["collective_learning_benchmark_single_t0"], ["collective_learning_benchmark_single_t01"],
            ["collective_learning_benchmark_single_t02"],
            ["collective_learning_benchmark_share_t", "collective-panda-002.local"],
            ["collective_learning_benchmark_share_t", "collective-panda-008.local"],
            ["collective_learning_benchmark_share_t", "collective-panda-009.local"]]
    episode_length = [1, 1, 1, 1, 1, 1]
    p = DataProcessor()

    for i in range(len(tags)):
        print("Plotting " + str(tags[i]))
        add_plot_over_trials(host, tags[i], p, episode_length[i])

    plt.legend(
        ("Task_0_single", "Task_01_single", "Task_02_single", "Task_0_shared", "Task_01_shared", "Task_02_shared"))

    plt.ylim([0, 0.4])
    plt.xlabel("Trial [1]")
    plt.ylabel("Cost [1]")
    plt.show()


def plot_collective_benchmark_3():
    host = "collective-panda-002.local"
    tags = [["collective_learning_benchmark_single3_0"], ["collective_learning_benchmark_single3_01"],
            ["collective_learning_benchmark_single3_02"],
            ["collective_learning_benchmark_share3_10_ind", "collective-panda-002.local"],
            ["collective_learning_benchmark_share3_10_ind", "collective-panda-008.local"],
            ["collective_learning_benchmark_share3_10_ind", "collective-panda-009.local"]]
    p = DataProcessor()

    for i in range(len(tags)):
        add_plot_over_time(host, tags[i], p)

    plt.legend(("Task_0", "Task_01", "Task_02", "Task_0_shared", "Task_01_shared", "Task_02_shared"))

    plt.ylim([0, 0.4])
    plt.xlim([0, 70])
    plt.xlabel("Time [s]")
    plt.ylabel("Cost [1]")
    plt.show()


def add_plot_over_trials(host: str, tags: list, data_processor: DataProcessor, episode_length: int):
    results = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    cost = data_processor.get_average_cost(results, True, episode_length)
    plt.plot(cost)


def add_plot_over_time(host: str, tags: list, data_processor: DataProcessor):
    results = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    cost, confidence = data_processor.get_average_cost_over_time(results, decreasing=True)
    plt.plot(cost)


def plot_stuff_1():
    p = DataProcessor()

    tags = ["collective_learning_experiment_multi"]
    results = get_multiple_experiment_data("collective-panda-007.local", "insert_object", results_db="ml_results",
                                           filter={"meta.tags": {"$all": tags}})
    agent = "collective-panda-008"
    cost = p.get_average_cost_over_time(results, 2000, True, agent)
    # cost = p.get_average_cost(results, True, 1, agent)
    plt.plot(cost)

    tags = ["transfer_learning", "cylinder_60"]
    results = get_multiple_experiment_data("collective-control-001.local", "insert_object",
                                           results_db="transfer_base_v2", filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost_over_time(results, 2000, True)
    # cost = p.get_average_cost(results, True, 1)
    plt.plot(cost)

    plt.legend(("Shared", "Single"))

    plt.ylim([0, 1])
    plt.xlabel("Trial [1]")
    plt.ylabel("Normed Cost [1]")
    plt.show()


def plot_iros_learning(host="collective-control-001.local"):
    expert = {
        "move": {
            "cost": [5.8, 5.02, 0.37],
            "time": [6.17, 49.4, 30.4]
        },
        "turn": {
            "cost": [1.12, 0.74, 0.63],
            "time": [27, 15, 7]
        },
        "press_button": {
            "cost": [0.65],
            "time": [28]
        },
        "extraction": {
            "cost": [0.68, 0.37],
            "time": [28, 18]
        },
        "insertion": {
            "cost": [1.35, 1.16, 1.16, 1.16, 1.16, 0.66],
            "time": [36, 32, 26, 45, 5, 2]
        },
        "place": {
            "cost": [4.23, 3.01],
            "time": [22, 36]
        },
        "grab": {
            "cost": [5.01, 3.51, 3.51, 3.21],
            "time": [46, 78, 76, 26]
        }
    }

    p = DataProcessor()
    skills = ["move", "grab", "insert_object", "turn", "extraction", "place", "press_button"]
    tags2 = ["move", "grab", "insertion", "turn", "extraction", "place", "press_button"]

    fig, axes = plt.subplots(1, len(skills), sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0.2})

    for i in range(len(skills)):
        print("Fetching data for skill:" + skills[i])
        tags = [tags2[i]]
        results = get_multiple_experiment_data(host, skills[i], results_db="iros2021",
                                               filter={"meta.tags": {"$all": tags}})
        cost, confidence = p.get_average_cost_over_time(results, decreasing=True)
        cost = cost * 5
        axes[i].fill_between(np.linspace(0, len(cost), len(cost)), cost - confidence, cost + confidence * 5, alpha=0.2)
        axes[i].plot(cost, linewidth=2)
        axes[i].plot([0, len(cost)], [5, 5], color="black", linestyle="dashed")

        time = [expert[tags2[i]]["time"][0]]
        for j in range(1, len(expert[tags2[i]]["time"])):
            time.append(expert[tags2[i]]["time"][j] + time[j - 1])

        axes[i].plot(time, expert[tags2[i]]["cost"], "r^")

        axes[i].set_ylim(0, 10)
        axes[i].set_xlim(0, len(cost))
        axes[i].grid()
        axes[i].tick_params(axis="both", which="both", length=0)
        axes[i].set_title(skills[i], y=1.0, pad=-14)
        axes[i].set_xlabel("Time [s]")
        if i == 0:
            axes[i].set_ylabel("Cost [s]                  t_max + h")

    fig.set_size_inches(16, 3)
    plt.yticks(np.arange(0, 10, step=1))
    plt.savefig("iros_results.png", bbox_inches='tight', dpi=300)
    plt.suptitle("Skill Learning")
    plt.show()


def live_plotting(tags=["demo_learning"], robots = ["collective-panda-002", "collective-panda-004",
              "collective-panda-003", "collective-panda-008"]):
    from plotting.live_plotter import live_plot
    live_plot(robots, tags)


def print_std(host: str, task_type: str, database: str, tags: list):
    p = DataProcessor()
    results = get_multiple_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost_over_time(results, 1500, True)


def smooth(x, window_len=100, window='blackman'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    np.hanning, np.hamming, np.bartlett, np.blackman, np.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window_len < 3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    s = np.r_[x[window_len - 1:0:-1], x, x[-2:-window_len - 1:-1]]
    # print(len(s))
    if window == 'flat':  # moving average
        w = np.ones(window_len, 'd')
    else:
        w = eval('np.' + window + '(window_len)')

    y = np.convolve(w / w.sum(), s, mode='valid')
    return y


def get_mean_over_window(x: np.ndarray, width: float = 200) -> (np.ndarray, np.ndarray):
    rest = len(x) % width
    n_windows = int(np.floor(len(x) / width))
    x_mean = []
    x_std = []
    for i in range(n_windows):
        if i == n_windows - -1:
            x_mean.append(np.mean(x[i * width:]))
            x_std.append(np.mean(x[i * width:]))
        else:
            x_mean.append(np.mean(x[i*width:i*width + width]))
            x_std.append(np.mean(x[i * width:i * width + width]))

    print(x_mean)
    return np.asarray(x_mean), np.asarray(x_std)

def plot_horizontal_learning():
    robots = ["collective-panda-002","collective-panda-003","collective-panda-004","collective-panda-008","collective-panda-prime"]
    p = DataProcessor()

    tags = ["horizontal_learning_2"]
    experiments = ["n_immigrants="+str(n) for n in [0,2,4,6,8]]
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"][:len(experiments)]
    legend_handles1 = []
    legend_handles2 = []
    fig1, axes1 = plt.subplots(len(robots), 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    fig2, axes2 = plt.subplots(len(robots), 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2)
    fig3, axes3 = plt.subplots(len(robots), len(experiments), num=3)
    for r in range(len(robots)):
        for e in range(len(experiments)):
            filters = []
            filters.extend(tags)
            filters.append(experiments[e])
            print("tags = ", filters)
            results = get_multiple_experiment_data(robots[r], "insertion", filter={"meta.tags": {"$all": filters}})
            indexes2pop = []
            for i in range(len(results)):
                if len(results[i].trials) < 130:
                    print("no complete set. ",len(results[i].trials))
                    print(results[i].tags)
                    indexes2pop.append(i)
            indexes2pop.reverse()
            for i in indexes2pop:
                results.pop(i)
            #print("number of experiments = ", len(results))
            #statistic:
            statistic_dict = {}
            for agent in robots:
                statistic_dict[agent] = 0
            successes = []
            for res in results:
                for trial in res.trials:
                    if trial["q_metric"]["success"]:
                        successes.append(trial)
            for s in successes:
                if not s["external"]:
                    s["external"] = robots[r]
                statistic_dict[s["external"]] += 1
            pie_label = []
            pie_sizes = []
            for key in statistic_dict.keys():
                statistic_dict[key] = statistic_dict[key] / len(successes)
                if key == robots[r]:
                    pie_label.append("self")
                elif key[-3:] == "ime":
                    pie_label.append(key[-5:])
                else:
                    pie_label.append(key[-3:])
                pie_sizes.append(statistic_dict[key])
            print(statistic_dict)

            axes3[r,e].pie(pie_sizes, labels=pie_label, autopct='%1.1f%%')
            axes3[r,e].set_title(results[0].tags[1] + "\n" + experiments[e])

            
            # monocally decreasing cost:
            mean_cost, confidence = p.get_average_cost_over_trials(results, True, 1, specification="all")
            axes1[r].fill_between(np.linspace(1, len(mean_cost), len(mean_cost)), mean_cost - confidence, mean_cost + confidence * 5, alpha=0.2, color=colors[e])
            legend_handle1, = axes1[r].plot([i+1 for i in range(len(mean_cost))], mean_cost, linewidth=2, color=colors[e], label=experiments[e])
            legend_handles1.append(legend_handle1)

            axes1[r].set_ylim(0, 2.4)
            axes1[r].set_xlim(1, len(mean_cost))
            axes1[r].grid()
            axes1[r].tick_params(axis="both", which="both", length=0)
            xticks = [i*10 for i in range(1,(int(len(mean_cost)/10)) +1)]
            xticks.insert(0,1)
            axes1[r].set_xticks(xticks)
            axes1[r].set_title(results[0].tags[1], y=1.0, pad=-14)
            axes1[r].set_xlabel("Trial [1]")
            if r == 0:
                axes1[r].set_ylabel("Cost [1]")
                axes1[r].legend(legend_handles1, experiments, loc='upper right')#, experiments)
            
            # batchwise plot:
            mean_cost, confidence = p.get_average_cost_over_trials(results, False, 10, specification="all")
            axes2[r].fill_between(np.linspace(1, len(mean_cost), len(mean_cost)), mean_cost - confidence, mean_cost + confidence * 5, alpha=0.2, color=colors[e])
            legend_handle2, = axes2[r].plot([i+1 for i in range(len(mean_cost))], mean_cost, linewidth=2, color=colors[e], label=experiments[e])
            legend_handles2.append(legend_handle2)

            axes2[r].set_ylim(0, 2.4)
            axes2[r].set_xlim(1, len(mean_cost))
            axes2[r].grid()
            axes2[r].tick_params(axis="both", which="both", length=0)
            axes2[r].set_title(results[0].tags[1], y=1.0, pad=-14)
            axes2[r].set_xlabel("Trial [1]")
            if r == 0:
                axes2[r].set_ylabel("Cost [1]")
                axes2[r].legend(legend_handles2, experiments, loc='upper right')#, experiments)
    fig3.tight_layout()
    fig2.tight_layout()
    fig1.tight_layout()
    plt.show()

def get_iteration(tags:list):
    '''returns the tag containing the iteration number, like "n123" '''
    for tag in tags:
        if tag[0] == "n":
            try:
                iteration_n = int(tag[1:])
            except ValueError:
                continue
            return tag
def get_confidence(listoflists, confidence=0.95):
    '''calculates the everage and confidence-interval of listoflists'''
    longest_data = 0
    for data in listoflists:  # find longest data
        if len(data)>longest_data:
            longest_data = len(data)
    mean = []
    interval = []
    for i in range(longest_data):
        points = [x[i] for x in listoflists if i<len(x)]  # use just points for calculation that are available
        mean.append(np.mean(points))
        interval.append(st.t.interval(confidence=confidence, df=len(points)-1, loc=mean[-1], scale=st.sem(points)))
    return mean, interval

def get_confidence_time(listoflists, confidence=0.95, n_points=1000):
    '''calculates the everage and confidence-interval of listoflists (used for trials with timestemp)
        input: list of lists with (time, cost)
        n_points: resolution; How many points the output should have  
        output: mean, interval and time points (size = n_points)  
    '''
    if len(listoflists) < 1:
        return False, False, False
    longest_time = 0
    for data in listoflists:  # find longest time
        max_time_i = max([time for (time,cost) in data])  # max time for this iteration
        if max_time_i>longest_time:
            longest_time = max_time_i
    mean = []
    interval = []
    for time_i in np.linspace(0, ceil(longest_time), n_points):
        # calculate mean and interval for every time_i:
        temp = []
        for i in range(len(listoflists)):
            # append last cost entry before time_i
            trials_before_time = [trial for trial in listoflists[i] if trial[0] <= time_i]
            if trials_before_time:  # is not empty
                temp.append(trials_before_time[-1][1]) #append latest cost  
        if len(temp) <= 1:
            mean.append(float('nan'))
            interval.append(float('nan'))
        else:
            mean.append(np.mean(temp))
            interval.append(st.t.interval(confidence=confidence, df=len(temp)-1, loc=mean[-1], scale=st.sem(temp)))
    print(mean)
    for i in range(len(mean)-1,-1,-1):
        if mean[i] != mean[i]:
            mean[i] = mean[i+1]
        if interval[i] != interval[i]:
            interval[i] = interval[i+1]
    return mean, interval, np.linspace(0, ceil(longest_time), n_points)

def get_big_collective_data(tags:list = ["5agents_25tasks", "collective"], single_agent=False, cutoff=None, skip_module=set(), only_full_sets = True, monocally_decreasing=True,min_length=10):
    p = DataProcessor()
    if cutoff is None:  #plot old comparison
        # cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
        #             '003_left': 0.68016,
        #             '004_left': 0.74976,
        #             '005_left': 0.65, #
        #             '006_left': 0.6127199999999999,
        #             '007_left': 0.62616,
        #             '008_left': 0.6371999999999999,
        #             '010_left': 0.6888000000000001,
        #             '011_left': 0.63816,
        #             '012_left': 0.75528,
        #             '009_left': 0.6943199999999999,
        #             '013_left': 0.6348,
        #             '014_left': 0.6,
        #             '015_left': 0.68184,
        #             '016_left': 0.9,   #
        #             '017_left': 0.63864,
        #             #'018_left': 0.63144,  # '018_left': 0.63144,
        #             '041_left': 0.63144,
        #             '021_left': 0.63528,
        #             '022_left': 0.6828000000000001,
        #             '023_left': 0.6648000000000001,
        #             '024_left': 0.9187199999999999,
        #             '025_left': 0.64752,
        #             '027_left': 0.68448,
        #             '040_left':  0.61824,#'028_left': 0.61824,
        #             '029_left': 0.68088}
        modules = list_block_1 + list_block_2 + list_U
        cutoff = {}
        for m in modules:
            cutoff[m] = float("inf")
        modules.pop(modules.index("041"))
        modules.append("018")
    else:
        modules = list_block_1+list_block_2+list_U

    #getting data
    results_dict = {}
    max_instances = 0
    task_finished_times = []
    for xxx in modules:
        if xxx in skip_module:
            continue
        try:
            results = get_multiple_experiment_data("collective-"+xxx+".rsi.ei.tum.de", "insertion", "ml_results", {"meta.tags": tags})
        except DataNotFoundError:
            print("data not found on ",xxx)
            continue
        except ServerSelectionTimeoutError:
            continue
        print(len(results), "results found for ",xxx)
        for result in results:
            if result.instance[-6:] == "_table":
                result.instance = result.instance[:-6]
            iteration = get_iteration(result.tags)
            #if xxx == "001":
            #    print(xxx,"_left iterations",iteration, "best cost: ",min(result.costs))
            if len(result.costs)<min_length:
                print("less than ",min_length," trials. Skipping...")
                continue
            learning_time = result.get_time_until_threshold(cutoff[xxx])
            if not learning_time:
                #print(xxx," iteration",iteration, "didnt fully learn the task")
                learning_time = result.times[-1]
            if iteration not in results_dict.keys():
                results_dict[iteration] = { "earliest_starting_time":float('inf'), 
                                            "times_of_taskFinish":[], 
                                            "accumulated_costs_times":[], 
                                            "starting_times":[],
                                            "instances":[],
                                            "costs_times":[],
                                            "successes_times":[]}
            if result.instance in results_dict[iteration]["instances"]:  # ignore the whole iteration if is was done twice 
                print("ignore iteration because it was done twice")
                double_iteration_index = results_dict[iteration]["instances"].index(result.instance)
                results_dict.pop(iteration)
                continue
            if results_dict[iteration]["earliest_starting_time"] > result.starting_time:  # save lowest starting time
                results_dict[iteration]["earliest_starting_time"] = result.starting_time
            if monocally_decreasing: 
                monotonically_decreading_costs = p.get_monotonically_decreasing_cost(result.costs)
            else:
                monotonically_decreading_costs = result.costs
            times_costs = [(t,c) for t,c in zip(result.times, monotonically_decreading_costs)]  # list of tupels [(cost,time),(cost,time),...]
            results_dict[iteration]["accumulated_costs_times"].append(times_costs)
            results_dict[iteration]["costs_times"].append(times_costs)
            results_dict[iteration]["starting_times"].append(result.starting_time)
            results_dict[iteration]["times_of_taskFinish"].append(learning_time)
            results_dict[iteration]["instances"].append(result.instance)
            results_dict[iteration]["successes_times"].append(result.get_successes_per_time())
            
      #      sorted(results_dict[iteration]["accumulated_costs_times"])
      #  if xxx == "007":
      #      print(results_dict["n1"])
    max_instances = 0
    all_instaces = []
    #print(results_dict.keys())
    for r in results_dict.values():
        if len(r["instances"]) > max_instances:
            max_instances = len(r["instances"])
            all_instaces = r["instances"]

    #rearranging data for plotting and adding time offeset relative to experiment beginning
    for iteration in list(results_dict.keys()):
        results = results_dict[iteration]
        if len(results["instances"]) < max_instances and only_full_sets:
            missing = [x for x in all_instaces if x not in results["instances"]]
            print("pop iteration ",iteration, "\n" ,"missing instances: ",missing)
            del results_dict[iteration]
            continue
        accumulated_costs_times = []  # currently unused (was ment to plot the decreasing accumulated cost over time)
        for i in range(len(results["starting_times"])):
            if single_agent:  # only single agent at a time
                if i == 0:
                    time_offset = 0 
                else:
                    time_offset = results["times_of_taskFinish"][i-1] + 10  # time offset is finsihing time of last agents trial +10sec 
            else:  # normal time offset (no single isolated learning)
                time_offset = results["starting_times"][i] - results["earliest_starting_time"]
            times_costs_relative = [(cost, time+time_offset) for time, cost in results["accumulated_costs_times"][i]]  
            accumulated_costs_times.extend(times_costs_relative)
            results["times_of_taskFinish"][i] = results["times_of_taskFinish"][i] + time_offset
        
        if not single_agent:
            results["accumulated_costs_times"] = sorted(accumulated_costs_times)
            results["instances"] = [x[1] for x in sorted(zip(results["times_of_taskFinish"], results["instances"]))]  #same order as times_of_taskFinish (next line)
            results["times_of_taskFinish"] = sorted(results["times_of_taskFinish"])
        #print("instances ordered: \n","\n".join(results["instances"]))
    
    # create data for plotting
    times_of_finished_tasks = [results_dict[iteration]["times_of_taskFinish"] for iteration in results_dict]
    times_of_finished_tasks_mean, times_of_finished_tasks_confidence = get_confidence(times_of_finished_tasks)
    print("full set of experiments: ", len(times_of_finished_tasks))
    
    # inserting 0 at the beginning for better plotting
    times_of_finished_tasks_mean.insert(0,0)
    times_of_finished_tasks_confidence.insert(0,(0,0))
    return times_of_finished_tasks_mean, times_of_finished_tasks_confidence, results_dict


def get_global_collective_data(tags_list:list = [["10agents_25tasks", "collective", "n2",'ps_alpha_5'],["100collective",'ps_alpha_5']], 
                               single_agent=False, cutoff=None, skip_module=set(), store_data_ip:str = False):
    p = DataProcessor()
    tasks = {   
        "001":["001_left","D_007","D_016","D_017"],
        "003":["003_left","D_012","D_005","D_018","D_028"],
        "004":["004_left","D_019","D_020"],
        "005":["005_left","D_006", "D_026", "D_027"],
        "006":["006_left","D_002", "D_001", "D_021"],
        "007":["007_left","D_022","D_011"],
        "008":["008_left","D_008", "D_004","D_013"],
        "010":["010_left","D_009","D_014","D_024","D_025"],
        "011":["011_left","D_010", "D_015","D_023"],
        "012":["012_left","C_007","C_key_05","C_006"],
        "009":["009_left","A_015_trapezoid","B_017_IT2DE","B_013"],
        "013":["013_left","A_030_shamrock","A_012_ellipsoid-2", "C_011"],
        "014":["014_left","A_024_moon","C_020","B_016"],
        "015":["015_left","B_012_DE2DE","A_011","C_025"],
        "016":["016_left","A_026_cylinder_10","A_026_cylinder_20","A_026_cylinder_50","A_026_cylinder_30"],  #,,,],"A_026_cylinder_60"
        "017":["017_left","B_015","C_key_12","A_013_hexagram"],
        "041":["020_left","A_021_arrow","A_key_24","C_022"],
        "021":["021_left","C_018","A_020_pentagram","C_019"],
        "022":["022_left","C_010","C_013","C_009"],
        "023":["023_left","A_019_oneline","C_key_08","C_014"],
        "024":["024_left","C_017","C_015","C_key_24"],
        "025":["025_left","A_014_doji-1","A_023_stairs","A_025_heart"],
        "026":["B-014","A_022_diamond","B-018"],
        "027":["027_left","C_016","C_key_23","A_031_audi"],
        "040":["028_left"],
        "029":["029_left","A_016_sector","A_018_cross-2", "A_016_cross-1"]
        }
    if cutoff is None:  #plot old comparison
        cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088,
                    
                    }
        modules = list_block_1 + list_block_2 + list_U
        modules.pop(modules.index("041"))
        modules.append("018")

    else:
        modules = list_block_1+list_block_2+list_U

    #getting data
    results_dict = {}
    max_instances = 0
    task_finished_times = []
    for xxx in modules:
        if xxx in skip_module:
            continue
        results = []
        for tags in tags_list:
            try:
                results.extend(get_multiple_experiment_data("collective-"+xxx+".local", "insertion", "ml_results", {"meta.tags": tags}))  #.rsi.ei.tum.de
            except DataNotFoundError:
                print("data not found on ",xxx)
                continue
            except ServerSelectionTimeoutError:
                print("cannot connect to ",xxx)
        for r in results:
            print("found", r.tags, " on ",xxx)
        #print(len(results), "results found for ",xxx)
        for result in results:
            iteration = get_iteration(result.tags)
            #if xxx == "001":
            #    print(xxx,"_left iterations",iteration, "best cost: ",min(result.costs))
            if len(result.costs)<10:
                continue
            if xxx+"_left" in cutoff:
                learning_time = result.get_time_until_threshold(cutoff[xxx+"_left"])
            else:
                learning_time = result.get_time_until_threshold(0.8)
            if not learning_time:
                if len(result.times) > 300:
                    learning_time = result.times[299]
                    result.times = result.times[:300]
                else:
                    learning_time = result.times[-1]
            if iteration not in results_dict.keys():
                results_dict[iteration] = {}
            if xxx not in results_dict[iteration]:
                results_dict[iteration][xxx] = { "earliest_starting_time":float('inf'), 
                                            "times_of_taskFinish":[], 
                                            "accumulated_costs_times":[], 
                                            "starting_times":[],
                                            "instances":[],
                                            "first_success":[]}
            if not xxx in results_dict[iteration]:
                results_dict[iteration][xxx] = {}
            
            monotonically_decreading_costs = p.get_monotonically_decreasing_cost(result.costs)
            times_costs = [(t,c) for t,c in zip(result.times, monotonically_decreading_costs)]
            results_dict[iteration][xxx]["starting_times"].append(result.starting_time)
            results_dict[iteration][xxx]["times_of_taskFinish"].append(learning_time)
            results_dict[iteration][xxx]["instances"].append(result.instance)
            s_list,t_list =  result.get_successes_per_time()
            try:
                first_success = [t for s,t in zip(s_list,t_list) if s==True][0]
            except IndexError:
                first_success = result.times[-1]
            print("first_success: ", first_success)
            results_dict[iteration][xxx]["first_success"].append( first_success)

            
    for xxx in modules:
        if xxx not in results_dict:
            continue
        sort_this = zip(results_dict[iteration][xxx]["times_of_taskFinish"],results_dict[iteration][xxx]["instances"],results_dict[iteration][xxx]["starting_times"],results_dict[iteration][xxx]["fist_success"])
        this_is_sorted = sorted(sort_this, key=lambda x: tasks[xxx].index(x[1]))
        results_dict[iteration][xxx]["times_of_taskFinish"] = [x[0] for x in this_is_sorted]
        results_dict[iteration][xxx]["instances"] = [x[1] for x in this_is_sorted]
        results_dict[iteration][xxx]["starting_times"] = [x[2] for x in this_is_sorted]
        results_dict[iteration][xxx]["first_success"] = [x[3] for x in this_is_sorted]
      #      sorted(results_dict[iteration]["accumulated_costs_times"])
        #if xxx == "007":
        #    print(results_dict["n1"])
    max_instances = 0
    all_instaces = []
    #print(results_dict.keys())
    #for r in results_dict.values():
    #    if len(r["instances"]) > max_instances:
   #         max_instances = len(r["instances"])
   #         all_instaces = r["instances"]
    
    s = 0
    for instances in results_dict.keys():
        for key in results_dict[instances].keys():
            print(key, " instances: ", len(results_dict[instances][key]["instances"]))
            s += len(results_dict[instances][key]["instances"])
    print("total=",s)
    if store_data_ip:
        global_client = MongoDBClient(store_data_ip)
        global_client.write("pitstop_charlie","backup_plotting",{"results":results_dict,"tags":tags_list})
    #rearranging data for plotting and adding time offeset relative to experiment beginning
    results_dict2 = copy.deepcopy(results_dict)
    for iteration in list(results_dict.keys()):  # only one iteration assumed check if it works for more...
        currently_running = {}
        for m in results_dict2[iteration].keys():
            currently_running[m] = {"finishes_at":0,
                                    "tasks_count":0,
                                    "active":False}
        parallel_agents = 10
        agent_list = [(0,"host")]*parallel_agents

        task_finished_times = []
        first_successes = []
        stop_while = False
        time_from = False
        start_next = False
        lowest_time = 0
        available_modules =[]
        while len(results_dict2[iteration]) > 0:
            aktive_agents = 0
            # try:
            #     lowest_time = min([currently_running[x]["finishes_at"] for x in currently_running if currently_running[x]["finishes_at"] > 0])
                
            # except ValueError:
            #     print("cant all finsished_at are 0", currently_running)
            #     lowest_time = 0
            for xxx in results_dict[iteration]:
                if len(results_dict2[iteration]) == 0:
                    stop_while = True
                    break
                if xxx in results_dict2[iteration]:
                    if len(results_dict2[iteration][xxx]["times_of_taskFinish"]) == 0:
                        try:
                            results_dict2[iteration].pop(xxx)
                            currently_running[xxx]["finishes_at"] = float("inf")
                            # lowest_time = min([currently_running[x]["finishes_at"] for x in currently_running])
                            # print("reevaluate lowest time ", lowest_time,currently_running)
                        except KeyError:  #already poped
                            print("already poped", xxx)
                            pass
                        continue
                else:
                    continue
                active_agents = sum([currently_running[x]["active"] for x in currently_running])
                if active_agents < parallel_agents:
                    finished_time = results_dict2[iteration][xxx]["times_of_taskFinish"].pop(0)
                    first_success = results_dict2[iteration][xxx]["first_success"].pop(0)
                    if len(results_dict2[iteration][xxx]["times_of_taskFinish"]) == 0:
                        results_dict2[iteration].pop(xxx)
                    currently_running[xxx]["finishes_at"] = finished_time
                    currently_running[xxx]["active"] = True
                    task_finished_times.append(finished_time)
                    first_successes.append(first_success)
                    agent_list.pop(0)
                    agent_list.append((finished_time,xxx))
                    agent_list.sort(key=lambda x: x[0])

                    available_modules = []
                    for x in currently_running:
                        available_modules.append((currently_running[x]["finishes_at"], x))
                else:
                    pass
            #print("\n")
            #print(agent_list)
            lowest_time, agent = agent_list.pop(0)
            #print(agent, " finished at ", lowest_time)

            starting_time = copy.deepcopy(lowest_time)
            keys = list(results_dict2[iteration].keys())
            if len(keys) <= 0:
                break
            keys.reverse()
            start_next = False
            for x in keys:
                if currently_running[x]["finishes_at"] <= lowest_time:
                    lowest_time = currently_running[x]["finishes_at"]
                    start_next = (starting_time, x)
            if not start_next:
                lowest_time = float('inf')
                for x in results_dict2[iteration]:
                    if currently_running[x]["finishes_at"] < lowest_time:
                        lowest_time = currently_running[x]["finishes_at"]
                        start_next = (lowest_time, x)
            finished_time = results_dict2[iteration][start_next[1]]["times_of_taskFinish"].pop(0) + start_next[0] + 30
            first_success = results_dict2[iteration][start_next[1]]["first_success"].pop(0) + start_next[0] + 30
            
            if len(results_dict2[iteration][start_next[1]]["times_of_taskFinish"]) == 0:
                results_dict2[iteration].pop(start_next[1])

            task_finished_times.append(finished_time)
            first_successes.append(first_success)
            #print("starting on ",start_next[1], "unitl ",finished_time)
            agent_list.append((finished_time, start_next[1]))
            agent_list.sort(key=lambda x: x[0])
            currently_running[start_next[1]]["finishes_at"] = finished_time

            if stop_while:
                break
        
        
        task_finished_times = sorted(task_finished_times)
        first_successes = sorted(first_successes)

    print("full set of experiments: ", len(task_finished_times))
    print()
    
    # inserting 0 at the beginning for better plotting
    task_finished_times.insert(0,0)
    first_successes.insert(0,0)
    #times_of_finished_tasks_confidence.insert(0,(0,0))
    return task_finished_times, first_successes, s

def plot_big_collective():
    new_cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088}
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    plt.style.use('dark_background')
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    
    print("\ngetting collective data")
    mean_collective, confidence_collective = get_big_collective_data(["5agents_25tasks","collective"],cutoff=new_cutoff,skip_module=set(["018","010","020"]))  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    lower_bound_confindece_collective = [x[0]/60 for x in confidence_collective]
    upper_bound_confindece_collective = [x[1]/60 for x in confidence_collective]
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="collective knowledge sharing")
    axes1.fill_betweenx(range(len(mean_collective)), lower_bound_confindece_collective, upper_bound_confindece_collective, alpha=0.2)

    print("\ngetting collective data")
    mean_collective, confidence_collective = get_big_collective_data(["5agents_25tasks","collective","ps_alpha_5_reverse"],cutoff=new_cutoff,skip_module=set(["018","010","020"]))  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    lower_bound_confindece_collective = [x[0]/60 for x in confidence_collective]
    upper_bound_confindece_collective = [x[1]/60 for x in confidence_collective]
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="collective knowledge sharing\n(10 aoptimised sequence)",color="tab:pink")
    axes1.fill_betweenx(range(len(mean_collective)), lower_bound_confindece_collective, upper_bound_confindece_collective, alpha=0.2,color="tab:pink")
    print("\ngetting collective data")
    mean_collective, confidence_collective = get_big_collective_data(["5agents_25tasks","collective"],skip_module=set(["018","010","020"]))  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    lower_bound_confindece_collective = [x[0]/60 for x in confidence_collective]
    upper_bound_confindece_collective = [x[1]/60 for x in confidence_collective]
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="collective knowledge sharing (5 agents)")
    axes1.fill_betweenx(range(len(mean_collective)), lower_bound_confindece_collective, upper_bound_confindece_collective, alpha=0.2)
    print("\ngetting parallel isolated data")
    mean_isolated, confidence_isolated = get_big_collective_data(["5agents_25tasks_local","isolated_local_noFastPipeline"],skip_module=set(["018","010","020"]))  # history: ["5agents_25tasks_local","isolated_local_noFastPipeline"]
    mean_isolated = [x/60 for x in mean_isolated]
    lower_bound_confindece_isolated = [x[0]/60 for x in confidence_isolated]
    upper_bound_confindece_isolated = [x[1]/60 for x in confidence_isolated]
    legend_isolated = axes1.plot(mean_isolated, range(len(mean_isolated)), label="isolated parallel learning")
    axes1.fill_betweenx(range(len(mean_isolated)), lower_bound_confindece_isolated, upper_bound_confindece_isolated, alpha=0.2)
    print("\ngetting single isolated data")
    mean_isolated_single, confidence_isolated_single = get_big_collective_data(["5agents_25tasks_local","isolated_local_noFastPipeline"], single_agent=True,skip_module=set(["018","010","020"]))  #history: ["5agents_25tasks_local","isolated_local_noFastPipeline"]
    mean_isolated_single = [x/60 for x in mean_isolated_single]
    lower_bound_confindece_isolated_single = [x[0]/60 for x in confidence_isolated_single]
    upper_bound_confindece_isolated_single = [x[1]/60 for x in confidence_isolated_single]
    legend_isolated_single = axes1.plot(mean_isolated_single, range(len(mean_isolated_single)), label="isolated single learning",color = "tab:green")
    axes1.fill_betweenx(range(len(mean_isolated_single)), lower_bound_confindece_isolated_single, upper_bound_confindece_isolated_single, alpha=0.2,color = "tab:green")
    print(["\n5agents_25tasks_rearanged", "collective"])
    mean_collective_re, confidence_collective_re = get_big_collective_data(["5agents_25tasks_rearanged", "collective"],skip_module=set(["018","010","020"]))  # history: ["5agents_25tasks_rearanged", "collective"]
    mean_collective_re = [x/60 for x in mean_collective_re]
    lower_bound_confindece_collective_re = [x[0]/60 for x in confidence_collective_re]
    upper_bound_confindece_collective_re = [x[1]/60 for x in confidence_collective_re]
    legend_collective_re = axes1.plot(mean_collective_re, range(len(mean_collective_re)), label="collective knowledge sharing\n(5 agents, optimised sequence)",color="tab:red")
    axes1.fill_betweenx(range(len(mean_collective_re)), lower_bound_confindece_collective_re, upper_bound_confindece_collective_re, alpha=0.2,color="tab:red")
        
    

   
    axes1.set_xlabel("time [min]", fontsize=14)
    axes1.set_ylabel("learned skills [1]", fontsize=14)
    axes1.set_title("learn 25 skills", fontsize=14)
    axes1.set_xlim((0,700))
    #axes1.set_xlim((0,220))
    axes1.grid()
    axes1.legend(loc="center right", fontsize=14)  #lower right
    plt.show(block=False)


def plot_100_collective(global_ip = False):
    new_cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088}
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    plt.style.use('dark_background')
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    
    # print("\ngetting collective data")
    # mean_collective, confidence_collective = get_big_collective_data(["10agents_25tasks","collective","ps_alpha_5"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    # mean_collective = [x/60 for x in mean_collective]
    # lower_bound_confindece_collective = [x[0]/60 for x in confidence_collective]
    # upper_bound_confindece_collective = [x[1]/60 for x in confidence_collective]
    # legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="collective knowledge sharing (10 agents)")
    # axes1.fill_betweenx(range(len(mean_collective)), lower_bound_confindece_collective, upper_bound_confindece_collective, alpha=0.2)


    print("\ngetting 100 collective data")
    mean_collective, first_successes, n_tasks = get_global_collective_data(cutoff=new_cutoff,skip_module=set(["018","010","020"]),store_data_ip=global_ip)  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    first_successes = [x/60 for x in first_successes]
    print(len(first_successes)," vs ", len(mean_collective))
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="pitstop_charlie (ICRA)\n(25 agents, %i objects)"%n_tasks, color="tab:blue",linewidth=2)
    #legend_collective = axes1.plot(first_successes, range(len(first_successes)), label="first successes(10 agents, %i objects)"%n_tasks, color="tab:olive",linewidth=2)
    
    print("\ngetting 100 collective data")
    mean_collective, first_successes, n_tasks = get_global_collective_data(tags_list=[["ps_charlie_2"]],cutoff=new_cutoff,skip_module=set(["018","010","020"]),store_data_ip=global_ip)  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    first_successes = [x/60 for x in first_successes]
    print(len(first_successes)," vs ", len(mean_collective))
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="pitstop_charlie\n(15 agents, %i objects)"%n_tasks, color="tab:cyan",linewidth=2)
    #legend_collective = axes1.plot(first_successes, range(len(first_successes)), label="first successes(10 agents, %i objects)"%n_tasks, color="tab:olive",linewidth=2)
    print("\ngetting 100 collective data")
    mean_collective, first_successes, n_tasks = get_global_collective_data(tags_list=[["ps_charlie_test", "n2"]],cutoff=new_cutoff,skip_module=set(["018","010","020"]),store_data_ip=global_ip)  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    first_successes = [x/60 for x in first_successes]
    print(len(first_successes)," vs ", len(mean_collective))
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="pitstop_charlie\n(15 agents, %i objects)"%n_tasks, color="tab:olive",linewidth=2)
    #legend_collective = axes1.plot(first_successes, range(len(first_successes)), label="first successes(10 agents, %i objects)"%n_tasks, color="tab:olive",linewidth=2)
    print("\ngetting 100 collective data")
    mean_collective, first_successes, n_tasks = get_global_collective_data(tags_list=[["ps_charlie_test", "n3"]],cutoff=new_cutoff,skip_module=set(["018","010","020"]),store_data_ip=global_ip)  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    first_successes = [x/60 for x in first_successes]
    print(len(first_successes)," vs ", len(mean_collective))
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="pitstop_charlie\n(15 agents, %i objects)"%n_tasks, color="tab:orange",linewidth=2)
    #legend_collective = axes1.plot(first_successes, range(len(first_successes)), label="first successes(10 agents, %i objects)"%n_tasks, color="tab:olive",linewidth=2)
    print("\ngetting 100 collective data")
    mean_collective, first_successes, n_tasks = get_global_collective_data(tags_list=[["ps_charlie_test", "n4"]],cutoff=new_cutoff,skip_module=set(["018","010","020"]),store_data_ip=global_ip)  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    first_successes = [x/60 for x in first_successes]
    print(len(first_successes)," vs ", len(mean_collective))
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="pitstop_charlie\n(15 agents, %i objects)"%n_tasks, color="tab:grey",linewidth=2)
    #legend_collective = axes1.plot(first_successes, range(len(first_successes)), label="first successes(10 agents, %i objects)"%n_tasks, color="tab:olive",linewidth=2)
    print("\ngetting 100 collective data")
    mean_collective, first_successes, n_tasks = get_global_collective_data(tags_list=[["ps_charlie_test","n6"]],cutoff=new_cutoff,skip_module=set(["018","010","020"]),store_data_ip=global_ip)  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    first_successes = [x/60 for x in first_successes]
    print(len(first_successes)," vs ", len(mean_collective))
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="pitstop_charlie\n(15 agents, %i objects)"%n_tasks, color="tab:brown",linewidth=2)
    #legend_collective = axes1.plot(first_successes, range(len(first_successes)), label="first successes(10 agents, %i objects)"%n_tasks, color="tab:olive",linewidth=2)
    mean_collective, first_successes, n_tasks = get_global_collective_data(tags_list=[["ps_charlie_test","n7"]],cutoff=new_cutoff,skip_module=set(["018","010","020"]),store_data_ip=global_ip)  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    first_successes = [x/60 for x in first_successes]
    print(len(first_successes)," vs ", len(mean_collective))
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="pitstop_charlie\n(15 agents, %i objects)"%n_tasks, color="tab:purple",linewidth=2)
    #legend_collective = axes1.plot(first_successes, range(len(first_successes)), label="first successes(10 agents, %i objects)"%n_tasks, color="tab:olive",linewidth=2)
    mean_collective, first_successes, n_tasks = get_global_collective_data(tags_list=[["ps_charlie_test","n8"]],cutoff=new_cutoff,skip_module=set(["018","010","020"]),store_data_ip=global_ip)  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    first_successes = [x/60 for x in first_successes]
    print(len(first_successes)," vs ", len(mean_collective))
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="pitstop_charlie\n(15 agents, %i objects)"%n_tasks, color="w",linewidth=2)
    #legend_collective = axes1.plot(first_successes, range(len(first_successes)), label="first successes(10 agents, %i objects)"%n_tasks, color="tab:olive",linewidth=2)

    print("\ngetting collective data")
    mean_collective, confidence_collective = get_big_collective_data(["10agents_25tasks","collective","ps_alpha_5_reverse"],cutoff=new_cutoff,skip_module=set(["018","010","020"]))  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    lower_bound_confindece_collective = [x[0]/60 for x in confidence_collective]
    upper_bound_confindece_collective = [x[1]/60 for x in confidence_collective]
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="pitstop_alpha\n(10 agents)",color="tab:pink",linewidth=2)
    axes1.fill_betweenx(range(len(mean_collective)), lower_bound_confindece_collective, upper_bound_confindece_collective, alpha=0.2,color="tab:pink")
    # print("\ngetting collective data")
    # mean_collective, confidence_collective = get_big_collective_data(["5agents_25tasks","collective"],skip_module=set(["018","010","020"]))  # history: ["5agents_25tasks","collective"]
    # mean_collective = [x/60 for x in mean_collective]
    # lower_bound_confindece_collective = [x[0]/60 for x in confidence_collective]
    # upper_bound_confindece_collective = [x[1]/60 for x in confidence_collective]
    # legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="collective knowledge sharing (5 agents)")
    # axes1.fill_betweenx(range(len(mean_collective)), lower_bound_confindece_collective, upper_bound_confindece_collective, alpha=0.2)
    #print("\ngetting parallel isolated data")
    #mean_isolated, confidence_isolated = get_big_collective_data(["5agents_25tasks_local","isolated_local_noFastPipeline"])  # history: ["5agents_25tasks_local","isolated_local_noFastPipeline"]
    #mean_isolated = [x/60 for x in mean_isolated]
    #lower_bound_confindece_isolated = [x[0]/60 for x in confidence_isolated]
    #upper_bound_confindece_isolated = [x[1]/60 for x in confidence_isolated]
    #legend_isolated = axes1.plot(mean_isolated, range(len(mean_isolated)), label="isolated parallel learning")
    #axes1.fill_betweenx(range(len(mean_isolated)), lower_bound_confindece_isolated, upper_bound_confindece_isolated, alpha=0.2)
    print("\ngetting single isolated data")
    mean_isolated_single, confidence_isolated_single = get_big_collective_data(["5agents_25tasks_local","isolated_local_noFastPipeline"], single_agent=True,skip_module=set(["018","010","020"]))  #history: ["5agents_25tasks_local","isolated_local_noFastPipeline"]
    mean_isolated_single = [x/60 for x in mean_isolated_single]
    lower_bound_confindece_isolated_single = [x[0]/60 for x in confidence_isolated_single]
    upper_bound_confindece_isolated_single = [x[1]/60 for x in confidence_isolated_single]
    legend_isolated_single = axes1.plot(mean_isolated_single, range(len(mean_isolated_single)), label="isolated single learning",color = "tab:green",linewidth=2)
    axes1.fill_betweenx(range(len(mean_isolated_single)), lower_bound_confindece_isolated_single, upper_bound_confindece_isolated_single, alpha=0.2,color = "tab:green")
    print(["\n5agents_25tasks_rearanged", "collective"])
    mean_collective_re, confidence_collective_re = get_big_collective_data(["5agents_25tasks_rearanged", "collective"],skip_module=set(["018","010","020"]))  # history: ["5agents_25tasks_rearanged", "collective"]
    mean_collective_re = [x/60 for x in mean_collective_re]
    lower_bound_confindece_collective_re = [x[0]/60 for x in confidence_collective_re]
    upper_bound_confindece_collective_re = [x[1]/60 for x in confidence_collective_re]
    legend_collective_re = axes1.plot(mean_collective_re, range(len(mean_collective_re)), label="pitstop_alpha\n(5 agents)",color="tab:red",linewidth=2)
    axes1.fill_betweenx(range(len(mean_collective_re)), lower_bound_confindece_collective_re, upper_bound_confindece_collective_re, alpha=0.2,color="tab:red")
        
        
    axes1.set_xlabel("time [min]", fontsize=14)
    axes1.set_ylabel("learned skills [1]", fontsize=14)
    axes1.set_title("learn %i skills"%n_tasks, fontsize=14)
    axes1.set_xlim((0,700))
    axes1.set_xlim((0,220))
    axes1.set_ylim((0,100))
    axes1.grid()
    axes1.legend(loc="center right", fontsize=14)  #lower right
    plt.show(block=False)

    fig2, axes2 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2)
    print(first_successes)
    legend_collective = axes2.plot(first_successes, range(len(first_successes)), label="first successes(10 agents, %i objects)"%n_tasks,linewidth=2)
    axes2.set_title("first successes (100 skills)")
    axes2.set_xlabel("time [min]", fontsize=14)
    axes2.set_ylabel("first successful trial [1]", fontsize=14)
    axes2.set_title("learn %i skills"%n_tasks, fontsize=14)
    axes2.set_xlim((0,700))
    axes2.set_xlim((0,220))
    axes2.set_ylim((0,100))
    axes2.legend(loc="lower right", fontsize=14) 
    axes2.grid()

    plt.show()



def plot_alpha_transfer():
    new_cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088}
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    plt.style.use('dark_background')
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    
    print("\ngetting single isolated data")
    mean_isolated_single, confidence_isolated_single, results_dict_single = get_big_collective_data(['noKnowledge', 'noSharing', 'isolated',], single_agent=False, skip_module=set(["028", "018","010"])) 
    mean_isolated_single = [x/60 for x in mean_isolated_single]
    lower_bound_confindece_isolated_single = [x[0]/60 for x in confidence_isolated_single]
    upper_bound_confindece_isolated_single = [x[1]/60 for x in confidence_isolated_single]
    legend_isolated_single = axes1.plot(mean_isolated_single, range(len(mean_isolated_single)), label="isolated single learning (PSP)")
    axes1.fill_betweenx(range(len(mean_isolated_single)), lower_bound_confindece_isolated_single, upper_bound_confindece_isolated_single, alpha=0.2)
    print("\ngetting alpha transfer  data")
    mean_isolated_alpha, confidence_isolated_alpha, results_dict_alpha = get_big_collective_data(["alpha_task_transfer","default_context"], single_agent=False, skip_module=set(["028", "018","010"])) 
    mean_isolated_alpha = [x/60 for x in mean_isolated_alpha]
    lower_bound_confindece_isolated_alpha = [x[0]/60 for x in confidence_isolated_alpha]
    upper_bound_confindece_isolated_alpha = [x[1]/60 for x in confidence_isolated_alpha]
    legend_isolated_alpha = axes1.plot(mean_isolated_alpha, range(len(mean_isolated_alpha)), label="alpha task transfer, isolated (PSP)")
    axes1.fill_betweenx(range(len(mean_isolated_alpha)), lower_bound_confindece_isolated_alpha, upper_bound_confindece_isolated_alpha, alpha=0.2)
    

    print("\ngetting single isolated data CMAES")
    mean_isolated_single, confidence_isolated_single, results_dict_single_cmaes = get_big_collective_data(["isolated", "CMAES", "25Tasks", "9ind20gen","additional_run"], single_agent=False, skip_module=set(["028", "018","010","023"])) 
    mean_isolated_single = [x/60 for x in mean_isolated_single]
    lower_bound_confindece_isolated_single = [x[0]/60 for x in confidence_isolated_single]
    upper_bound_confindece_isolated_single = [x[1]/60 for x in confidence_isolated_single]
    legend_isolated_single = axes1.plot(mean_isolated_single, range(len(mean_isolated_single)), label="isolated single learning (CMA-ES)")
    axes1.fill_betweenx(range(len(mean_isolated_single)), lower_bound_confindece_isolated_single, upper_bound_confindece_isolated_single, alpha=0.2)
    print("\ngetting alpha transfer  data CMAES")
    mean_isolated_alpha, confidence_isolated_alpha, results_dict_alpha_cmaes = get_big_collective_data(["alpha_task_transfer_cmaes","default_context"], single_agent=False, skip_module=set(["028", "018","010"])) 
    mean_isolated_alpha = [x/60 for x in mean_isolated_alpha]
    lower_bound_confindece_isolated_alpha = [x[0]/60 for x in confidence_isolated_alpha]
    upper_bound_confindece_isolated_alpha = [x[1]/60 for x in confidence_isolated_alpha]
    legend_isolated_alpha = axes1.plot(mean_isolated_alpha, range(len(mean_isolated_alpha)), label="alpha task transfer, isolated (CMA-ES)")
    axes1.fill_betweenx(range(len(mean_isolated_alpha)), lower_bound_confindece_isolated_alpha, upper_bound_confindece_isolated_alpha, alpha=0.2)
    
    fig2, axes2 = plt.subplots(6, 4, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=2)
    results = {}
    for iter in results_dict_alpha.keys():
        for i in range(len(results_dict_alpha[iter]["instances"])):
            instance = results_dict_alpha[iter]["instances"][i]
            if instance not in results:
                results[instance] = {"alpha":[], "isolated":[], "alpha_cmaes":[], "isolated_cmaes":[]}
            results[instance]["alpha"].append(results_dict_alpha[iter]["costs_times"][i])
            index_isolated = results_dict_single[iter]["instances"].index(instance)
            results[instance]["isolated"].append(results_dict_single[iter]["costs_times"][index_isolated])
            
            if iter in results_dict_alpha_cmaes:
                try:
                    index_alpha_cmaes = results_dict_alpha_cmaes[iter]["instances"].index(instance)
                    results[instance]["alpha_cmaes"].append(results_dict_alpha_cmaes[iter]["costs_times"][index_alpha_cmaes])
                except ValueError:
                    pass
            if iter in results_dict_single_cmaes:
                try:
                    index_isolated_cmaes = results_dict_single_cmaes[iter]["instances"].index(instance)
                    results[instance]["isolated_cmaes"].append(results_dict_single_cmaes[iter]["costs_times"][index_isolated_cmaes])
                except ValueError:
                    pass

    for i, instance in enumerate(results.keys()):
        mean, interval, time_points = get_confidence_time(results[instance]["isolated"], n_points=1000)
        time_points = [s/60 for s in time_points]
        label = labels[modules.index(instance[:3])]
        axes2[i%6,int(i/6)].set_title(label)
        line_psp_no = axes2[i%6,int(i/6)].plot(time_points, mean, label = "no Knowledge, PSP")
        lower_confidence = [x[0] for x in interval]
        upper_confidence = [x[1] for x in interval]
        axes2[i%6,int(i/6)].fill_between(time_points, lower_confidence, upper_confidence, alpha=0.2)

        mean, interval, time_points = get_confidence_time(results[instance]["alpha"], n_points=1000)
        time_points = [s/60 for s in time_points]
        label = labels[modules.index(instance[:3])]
        axes2[i%6,int(i/6)].set_title(label)
        line_psp_alpha = axes2[i%6,int(i/6)].plot(time_points, mean, label = "alpha, PSP")
        lower_confidence = [x[0] for x in interval]
        upper_confidence = [x[1] for x in interval]
        axes2[i%6,int(i/6)].fill_between(time_points, lower_confidence, upper_confidence, alpha=0.2)

        if results[instance]["isolated_cmaes"]:
            mean, interval, time_points = get_confidence_time(results[instance]["isolated_cmaes"], n_points=1000)
            time_points = [s/60 for s in time_points]
            label = labels[modules.index(instance[:3])]
            axes2[i%6,int(i/6)].set_title(label)
            line_cmaes_no = axes2[i%6,int(i/6)].plot(time_points, mean, label = "no Knowledge, CMA-ES")
            lower_confidence = [x[0] for x in interval]
            upper_confidence = [x[1] for x in interval]
            axes2[i%6,int(i/6)].fill_between(time_points, lower_confidence, upper_confidence, alpha=0.2)
        if results[instance]["alpha_cmaes"]:
            mean, interval, time_points = get_confidence_time(results[instance]["alpha_cmaes"], n_points=1000)
            time_points = [s/60 for s in time_points]
            label = labels[modules.index(instance[:3])]
            axes2[i%6,int(i/6)].set_title(label)
            line_cmaes_alpha = axes2[i%6,int(i/6)].plot(time_points, mean, label = "alpha, CMA-ES")
            lower_confidence = [x[0] for x in interval]
            upper_confidence = [x[1] for x in interval]
            axes2[i%6,int(i/6)].fill_between(time_points, lower_confidence, upper_confidence, alpha=0.2)

        #axes2[i%6,int(i/6)].legend(loc="upper right")
        axes2[i%6,int(i/6)].set_ylim((0,2))
        axes2[i%6,int(i/6)].set_xlabel("time [min]")
        axes2[i%6,int(i/6)].set_ylabel("cost [1]")
    
    #lines = []
    #legend_texts = []
    #for ax in axes2: 
    #    Line, Label = ax.get_legend_handles_labels() 
    #    # print(Label) 
    #    lines.extend(Line) 
    #    legend_texts.extend(Label) 
    #fig2.legend(lines, legend_texts, loc="bottom right")
    lines, texts = axes2[0,2].get_legend_handles_labels()
    fig2.legend(lines, texts, loc = "lower right")
    print("130 trials for each run (alpha and noKnowledge)")

    axes1.set_xlabel("time [min]", fontsize=14)
    axes1.set_ylabel("learned skills [1]", fontsize=14)
    axes1.set_title("alpha task transfer VS no knowledge", fontsize=14)
    axes1.set_xlim((0,55))
    axes1.grid()
    axes1.legend(loc="lower right", fontsize=14)
    plt.show()


def plot_robustness_test():
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    plt.style.use('dark_background')
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    labels = ["IEC(C7)", "Triangle-1", "Hexagon-1", "USB-1", "Triangle-2", "Cylinder-1", "Key-1", "Plug(type F)-1", "Audio Jack(3.5mm)", "IEC(C13)", "Cylinder-2", "Hexagon-2", "HDMI-1", "Key-2", "Cylinder-3", "Square-1", "Hexagon-3", "Square-2", "Audio jack(6.35mm)", "USB-2", "Plug(type C)", "Key-3", "Plug(type F)-2", "HDMI-2", "Key-4"]
    modules = list_block_1 + list_block_2 + list_U

    print("\ngetting alpha transfer  data CMAES")
    # ["robustness_test","n2"]
    mean_reboot, confidence_reboot, reboot = get_big_collective_data(["robustness_test","n2"], single_agent=True, skip_module=set(["028", "018","010","029","017","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90) 
    print("\ngetting alpha transfer  data CMAES")
    # ["robustness_test","n2"]
    mean_isolated_alpha, confidence_isolated_alpha, directly = get_big_collective_data(["robustness_test","directly_after_learning"], single_agent=True, skip_module=set(["028", "018","010","029","017","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
    fig2, axes2 = plt.subplots(6, 5, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=2)
    results = {}
    successrate_reboot = {}
    successrate_directly = {}
    print(reboot.keys())
    print(directly.keys())
    for iter in reboot.keys():
        for i in range(len(reboot[iter]["instances"])):
            instance = reboot[iter]["instances"][i]
            print("instance: ", i, instance, iter)
            if instance not in results:
                results[instance] = {"alpha":[]}
            results[instance]["alpha"].append(reboot[iter]["costs_times"][i])
            successrate_reboot[instance] = reboot[iter]["successes_times"][i]
    for iter in directly.keys():
        for i in range(len(directly[iter]["instances"])):
            instance = directly[iter]["instances"][i]
            print("instance: ", i, instance, iter)
            if instance not in results:
                results[instance] = {"beta":[]}
            if "beta" not in results[instance]:
                results[instance]["beta"] = []
            results[instance]["beta"].append(directly[iter]["costs_times"][i])
            successrate_directly[instance] = directly[iter]["successes_times"][i]

    x = np.arange(len(results)) / 100  # the label locations
    width = 0.005  # the width of the bars
    multiplier = 0
    for i, instance in enumerate(results.keys()):
        offset = width*multiplier
        #mean, interval, time_points = get_confidence_time(results[instance]["alpha"], n_points=1000)
        #time_points = [s/60 for s in time_points]
        label = instance
        axes2[i%6,int(i/6)].set_title(label)
        try:
            times = [time/60 for time,cost in results[instance]["alpha"][0]]
            costs = [cost for time,cost in results[instance]["alpha"][0]]
            line_psp_r = axes2[i%6,int(i/6)].plot(times,costs, label = "after some days")
            
            successrate = sum(successrate_reboot[instance][0])/len(successrate_reboot[instance][0]) *100
            print(instance, "number of sets (rebooted): ",len(results[instance]["alpha"]), " successrate=",successrate)
            rects = axes1.bar(x + offset, successrate, width, label="after some days")
            axes1.bar_label(rects, padding=3)
        except KeyError:
            print("no reboot data for ",instance)
            pass  
        try:          
            times = [time/60 for time,cost in results[instance]["beta"][0]]
            costs = [cost for time,cost in results[instance]["beta"][0]]
            line_psp_d = axes2[i%6,int(i/6)].plot(times,costs, label = "directly after learning")
            successrate = sum(successrate_directly[instance][0])/len(successrate_directly[instance][0]) *100
            #print(successrate_directly[instance])
            print(instance, "number of sets (directly): ",len(results[instance]["alpha"]), " successrate=",successrate)
            rects = axes1.bar(x + offset, successrate, width, label="directly after learning")
            axes1.bar_label(rects, padding=3)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        multiplier+=1

        #lower_confidence = [x[0] for x in interval]
        #upper_confidence = [x[1] for x in interval]
        #axes2[i%6,int(i/6)].fill_between(time_points, lower_confidence, upper_confidence, alpha=0.2)

        axes2[i%6,int(i/6)].set_ylim((0,2.5))
        axes2[i%6,int(i/6)].set_xlabel("time [min]")
        axes2[i%6,int(i/6)].set_ylabel("cost [1]")
    
    lines, texts = axes2[0,2].get_legend_handles_labels()
    fig2.legend(lines, texts, loc = "lower right")
    fig2.suptitle("Robustness Test - Repeat best trial 100 times")
    print("130 trials for each run (alpha and noKnowledge)")

    axes1.set_xlabel("skill solution", fontsize=14)
    axes1.set_ylabel("success rate [%]", fontsize=14)
    axes1.set_title("alpha task transfer VS no knowledge", fontsize=14)
    axes1.set_xticks(x + width, list(results.keys()))
    axes1.grid()
    axes1.legend(loc="lower right", fontsize=14)
    plt.show()



def plot_convergence_test():
    plot_single_figures = False
    colors = ['#8dd3c7', '#feffb3', '#bfbbd9', '#fa8174', '#81b1d2', '#fdb462', '#b3de69', '#bc82bd', '#ccebc4', '#ffed6f']
    plt.style.use('dark_background')
    labels = ["IEC(C7)", "Triangle-1", "Hexagon-1", "USB-1", "Triangle-2", "Cylinder-1", "Key-1", "Plug(type F)-1", "Audio Jack(3.5mm)", "IEC(C13)", "Cylinder-2", "Hexagon-2", "HDMI-1", "Key-2", "Cylinder-3", "Square-1", "Hexagon-3", "Square-2", "Audio jack(6.35mm)", "USB-2", "Plug(type C)", "Key-3", "Plug(type F)-2", "HDMI-2", "Key-4"]
    modules = list_block_1 + list_block_2 + list_U
    fig2, axes2 = plt.subplots(6, 4, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=100)
    results = None
    # try:
    #     print("searching on collective NAS")
    #     client = MongoDBClient("10.157.175.119")
    #     results = client.read("plotting","convergence_test",{})
    #     if len(results) > 0:
    #         results = results[-1]
    #         results.pop("_id")
    #         print("found results on collective NAS")
    #     else:
    #         results = None
            
    # except:
    #     pass
    if results is None:
        # print("\ngetting default PSP data")
        # # ["robustness_test","n2"]
        # mean_reboot, confidence_reboot, reboot = get_big_collective_data(["convergence_test_1","5000"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90) 
        # print("\ngetting success check data (retry 5x) with PSP")
        # # ["robustness_test","n2"]
        # mean_isolated_alpha, confidence_isolated_alpha, directly = get_big_collective_data(["convergence_test_2","success_check"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        
        # print("\ngetting success check data (retry 5x) with CMA-ES")
        # # ["robustness_test","n2"]
        #mean_isolated_alpha, confidence_isolated_alpha, cmaes = get_big_collective_data(["convergence_test_3","success_check"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        # print("\ngetting success check data (retry 5x) with original PSP")
        # # ["robustness_test","n2"]
        # mean_isolated_alpha, confidence_isolated_alpha, origPSP = get_big_collective_data(["convergence_test_5","success_check"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        # mean_isolated_alpha, confidence_isolated_alpha, cartHold = get_big_collective_data(["convergence_test_6","success_check","holdpose"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        # mean_isolated_alpha, confidence_isolated_alpha, jointHold = get_big_collective_data(["convergence_test_6","success_check","jointpose"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        #mean_isolated_alpha, confidence_isolated_alpha, lifted_jointHold = get_big_collective_data(["convergence_test_7","success_check","lifted_jointpose"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        #mean_isolated_alpha, confidence_isolated_alpha, table_insertion = get_big_collective_data(["convergence_test_9","success_check","table_insertion"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        # #mean_isolated_alpha, confidence_isolated_alpha, mod_length_insertion = get_big_collective_data(["convergence_test_10","table_insertion"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        #mean_isolated_alpha, confidence_isolated_alpha, new_mount_table = get_big_collective_data(["convergence_test_10.2","modify_length"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        #mean_isolated_alpha, confidence_isolated_alpha, new_mount_table_decreasing = get_big_collective_data(["convergence_test_10.2","modify_length"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=True, only_full_sets=False,min_length=90)  
        #mean_isolated_alpha, confidence_isolated_alpha, new_mount_table_gmm8 = get_big_collective_data(["convergence_test_10.3","modify_length"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        #changes on origPSP
        #mean_isolated_alpha, confidence_isolated_alpha, new_mount_table_PSPenhanced = get_big_collective_data(["convergence_test_11","modify_length"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=90)  
        #florians last changes on origPSP
        mean_isolated_alpha, confidence_isolated_alpha, new_mount_table_florian = get_big_collective_data(["convergence_test_12","modify_length"], single_agent=True, skip_module=set(["028", "018","010","029","016","040"]),monocally_decreasing=False, only_full_sets=False,min_length=10)  
        
        results = {}
        successrate_reboot = {}
        successrate_directly = {}
        successrate_cmaes = {}
        successrate_origPSP = {}
        #print(reboot.keys())
        #print(directly.keys())
        # for iter in reboot.keys():
        #     for i in range(len(reboot[iter]["instances"])):
        #         instance = reboot[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"defaultPSP":[]}
        #         results[instance]["defaultPSP"].append(reboot[iter]["costs_times"][i])
        # for iter in directly.keys():
        #     for i in range(len(directly[iter]["instances"])):
        #         instance = directly[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"defaultPSPsc":[]}
        #         if "beta" not in results[instance]:
        #             results[instance]["defaultPSPsc"] = []
        #         results[instance]["defaultPSPsc"].append(directly[iter]["costs_times"][i])
        # for iter in cmaes.keys():
        #     for i in range(len(cmaes[iter]["instances"])):
        #         instance = cmaes[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"cmaes":[]}
        #         if "cmaes" not in results[instance]:
        #             results[instance]["cmaes"] = []
        #         results[instance]["cmaes"].append(cmaes[iter]["costs_times"][i])
        # for iter in origPSP.keys():
        #     for i in range(len(origPSP[iter]["instances"])):
        #         instance = origPSP[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"origPSP":[]}
        #         if "origPSP" not in results[instance]:
        #             results[instance]["origPSP"] = []
        #         results[instance]["origPSP"].append(origPSP[iter]["costs_times"][i])
        # for iter in cartHold.keys():
        #     for i in range(len(cartHold[iter]["instances"])):
        #         instance = cartHold[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"cartHold":[]}
        #         if "cartHold" not in results[instance]:
        #             results[instance]["cartHold"] = []
        #         results[instance]["cartHold"].append(cartHold[iter]["costs_times"][i])
        # for iter in jointHold.keys():
        #     for i in range(len(jointHold[iter]["instances"])):
        #         instance = jointHold[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"jointHold":[]}
        #         if "jointHold" not in results[instance]:
        #             results[instance]["jointHold"] = []
        #         results[instance]["jointHold"].append(jointHold[iter]["costs_times"][i])
        # for iter in lifted_jointHold.keys():
        #     for i in range(len(lifted_jointHold[iter]["instances"])):
        #         instance = lifted_jointHold[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"lifted_jointHold":[]}
        #         if "lifted_jointHold" not in results[instance]:
        #             results[instance]["lifted_jointHold"] = []
        #         results[instance]["lifted_jointHold"].append(lifted_jointHold[iter]["costs_times"][i])
        # for iter in table_insertion.keys():
        #     for i in range(len(table_insertion[iter]["instances"])):
        #         instance = table_insertion[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"table_insertion":[]}
        #         if "table_insertion" not in results[instance]:
        #             results[instance]["table_insertion"] = []
        #         results[instance]["table_insertion"].append(table_insertion[iter]["costs_times"][i])
        # for iter in new_mount_table.keys():
        #     for i in range(len(new_mount_table[iter]["instances"])):
        #         instance = new_mount_table[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"new_mount_table":[]}
        #         if "new_mount_table" not in results[instance]:
        #             results[instance]["new_mount_table"] = []
        #         results[instance]["new_mount_table"].append(new_mount_table[iter]["costs_times"][i])
        # for iter in new_mount_table_gmm8.keys():
        #     for i in range(len(new_mount_table_gmm8[iter]["instances"])):
        #         instance = new_mount_table_gmm8[iter]["instances"][i]
        #         print("instance: ", i, instance, iter)
        #         if instance not in results:
        #             results[instance] = {"new_mount_table_gmm8":[]}
        #         if "new_mount_table_gmm8" not in results[instance]:
        #             results[instance]["new_mount_table_gmm8"] = []
        #         results[instance]["new_mount_table_gmm8"].append(new_mount_table_gmm8[iter]["costs_times"][i])
        for iter in new_mount_table_florian.keys():
            for i in range(len(new_mount_table_florian[iter]["instances"])):
                instance = new_mount_table_florian[iter]["instances"][i]
                print("instance: ", i, instance, iter)
                if instance not in results:
                    results[instance] = {"new_mount_table_florian":[]}
                if "new_mount_table_florian" not in results[instance]:
                    results[instance]["new_mount_table_florian"] = []
                results[instance]["new_mount_table_florian"].append(new_mount_table_florian[iter]["costs_times"][i])

    figures = [None for x in range(len(results))]
    axes = [None for x in range(len(results))]
    for i, instance in enumerate(results.keys()):
        label = instance
        axes2[i%6,int(i/6)].set_title(label)
        try:
            print(instance, i)
            times = [time/60 for time,cost in results[instance]["defaultPSP"][0]]
            costs = [cost for time,cost in results[instance]["defaultPSP"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            #line_psp_r = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[0], label = "PSP")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                #axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[0], label = "PSP")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[0], alpha=0.2)
        except KeyError:
            print("no reboot data for ",instance)
            pass  
        try:          
            times = [time/60 for time,cost in results[instance]["defaultPSPsc"][0]]
            costs = [cost for time,cost in results[instance]["defaultPSPsc"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            #line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[1], label = "PSP with success-check")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                #axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[1], label = "PSP with success-check")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[1], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        try:          
            times = [time/60 for time,cost in results[instance]["cmaes"][0]]
            costs = [cost for time,cost in results[instance]["cmaes"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color='white', label = "CMAES dualarm") # with success-check
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[2], label = "CMAES with success-check")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[2], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        try:          
            times = [time/60 for time,cost in results[instance]["origPSP"][0]]
            costs = [cost for time,cost in results[instance]["origPSP"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            #line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[3], label = "original PSP with nonlinear hold process")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[3], label = "original PSP with nonlinear hold process") #  with success-check
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[3], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        try:          
            times = [time/60 for time,cost in results[instance]["cartHold"][0]]
            costs = [cost for time,cost in results[instance]["cartHold"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            #line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[5], label = "original PSP with cartesian impedance Hold")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[5], label = "original PSP with cartesian Hold")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[3], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        try:          
            times = [time/60 for time,cost in results[instance]["jointHold"][0]]
            costs = [cost for time,cost in results[instance]["jointHold"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            #line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[6], label = "original PSP with joint impedance Hold")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[6], label = "original PSP with joint Hold")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[3], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        try:          
            times = [time/60 for time,cost in results[instance]["lifted_jointHold"][0]]
            costs = [cost for time,cost in results[instance]["lifted_jointHold"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[7], label = "original PSP with lifted joint impedance Hold")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[7], label = "original PSP with lifted joint Hold")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[3], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        try:          
            times = [time/60 for time,cost in results[instance]["table_insertion"][0]]
            costs = [cost for time,cost in results[instance]["table_insertion"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[8], label = "original PSP with table mount")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[8], label = "original PSP with table mount")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[3], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        try:          
            times = [time/60 for time,cost in results[instance]["new_mount_table"][0]]
            costs = [cost for time,cost in results[instance]["new_mount_table"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color='g', label = "table, new mount, freshly teached")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[9], label = "table, new mount, freshly teached")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[3], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        try:          
            times = [time/60 for time,cost in results[instance]["new_mount_table_gmm8"][0]]
            costs = [cost for time,cost in results[instance]["new_mount_table_gmm8"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color='r', label = "origPSP with 8 GMM components")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[9], label = "table, new mount, freshly teached")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[3], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass 
        try:          
            times = [time/60 for time,cost in results[instance]["new_mount_table_florian"][0]]
            costs = [cost for time,cost in results[instance]["new_mount_table_florian"][0]]
            batch_mean = []
            batch_std = []
            for index in range(0,len(costs)-9,10):  # remove "-9" for full plot
                batch_mean.append(np.mean(costs[index:index+10]))
                batch_std.append(np.std(costs[index:index+10]))
            line_psp_d = axes2[i%6,int(i/6)].plot(list(range(1,len(batch_mean)+1)),batch_mean, color='r', label = "origPSP with 8 GMM components")
            if plot_single_figures:
                if figures[i] is None:
                    figures[i], axes[i] = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=i)
                axes[i].plot(list(range(1,len(batch_mean)+1)),batch_mean, color=colors[9], label = "table, new mount, freshly teached")
                #axes[i].fill_between(range(len(batch_mean)), np.array(batch_mean)+np.array(batch_std), np.array(batch_mean)-np.array(batch_std), color=colors[3], alpha=0.2)
        except KeyError:
            print("no directly after learning data for ",instance)
            pass
        axes2[i%6,int(i/6)].set_ylim((0,2.5))
        axes2[i%6,int(i/6)].set_xlim((0,50))
        axes2[5,int(i/6)].set_xlabel("mean cost of batch")
        axes2[i%6,int(i/6)].set_ylabel("cost [1]")
        if figures[i] is not None:
            axes[i].set_ylim((0,2.5))
            axes[i].set_xlabel("mean cost of batch")
            axes[i].set_ylabel("cost [1]")
            axes[i].legend(loc="upper right")
            figures[i].suptitle("Convergence Test - 5000 Trials\n"+instance)
    print(figures)
    client = MongoDBClient("10.157.175.119")
    client.write("plotting","convergence_test",results)
    lines, texts = axes2[0,0].get_legend_handles_labels()
    fig2.legend(lines, texts, loc = "lower right")
    fig2.suptitle("Convergence Test - 5000 Trials")
    print("130 trials for each run (alpha and noKnowledge)")
    plt.show()

def plot_originalVScurrentPSP():
    cutoff = {  '001_left': 0.,   # best solution found *1.2
                    '003_left': 0,
                    '004_left': 0,
                    '005_left': 0, #
                    '006_left': 0,
                    '007_left': 0,
                    '008_left': 0,
                    '010_left': 0,
                    '011_left': 0,
                    '012_left': 0,
                    '009_left': 0,
                    '013_left': 0,
                    '014_left': 0,
                    '015_left': 0,
                    '016_left': 0,   #
                    '017_left': 0,
                    '018_left': 0,  # '018_left': 0.63144,
                    '021_left': 0,
                    '022_left': 0,
                    '023_left': 0,
                    '024_left': 0,
                    '025_left': 0,
                    '027_left': 0,
                    '028_left': 0,
                    '029_left': 0}
    labels = ["IEC(C7)", "Triangle-1", "Hexagon-1", "USB-1", "Triangle-2", "Cylinder-1", "Key-1", "Plug(type F)-1", "Audio Jack(3.5mm)", "IEC(C13)", "Cylinder-2", "Hexagon-2", "HDMI-1", "Key-2", "Cylinder-3", "Square-1", "Hexagon-3", "Square-2", "Audio jack(6.35mm)", "USB-2", "Plug(type C)", "Key-3", "Plug(type F)-2", "HDMI-2", "Key-4"]
    modules = list_block_1 + list_block_2 + list_U

    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    
    print("\ngetting currnt psp data")
    mean_isolated_single, confidence_isolated_single, results_dict_psp = get_big_collective_data(['noKnowledge', 'noSharing', 'isolated','PSP'], single_agent=False, skip_module=set(["028","003", "018","010","011","015", "036","023","024","025","026","027","041","029"]),only_full_sets=False, monocally_decreasing=True,cutoff=cutoff) 
    mean_isolated_single = [x/60 for x in mean_isolated_single]
    lower_bound_confindece_isolated_single = [x[0]/60 for x in confidence_isolated_single]
    upper_bound_confindece_isolated_single = [x[1]/60 for x in confidence_isolated_single]
    legend_isolated_single = axes1.plot(mean_isolated_single, range(len(mean_isolated_single)), label="current Version")
    axes1.fill_betweenx(range(len(mean_isolated_single)), lower_bound_confindece_isolated_single, upper_bound_confindece_isolated_single, alpha=0.2)
    print("\ngetting original psp  data")
    mean_isolated_alpha, confidence_isolated_alpha, results_dict_orig = get_big_collective_data(['noKnowledge', 'noSharing', 'isolated','origPSP'], single_agent=False, skip_module=set(["028","003", "018","010","011","015","036","023","024","025","026","027","041","029"]),only_full_sets=False, monocally_decreasing=True,cutoff=cutoff) 
    mean_isolated_alpha = [x/60 for x in mean_isolated_alpha]
    lower_bound_confindece_isolated_alpha = [x[0]/60 for x in confidence_isolated_alpha]
    upper_bound_confindece_isolated_alpha = [x[1]/60 for x in confidence_isolated_alpha]
    legend_isolated_alpha = axes1.plot(mean_isolated_alpha, range(len(mean_isolated_alpha)), label="original PSP")
    axes1.fill_betweenx(range(len(mean_isolated_alpha)), lower_bound_confindece_isolated_alpha, upper_bound_confindece_isolated_alpha, alpha=0.2)

    fig2, axes2 = plt.subplots(6, 2, sharex=True, gridspec_kw={'hspace': 0.5, 'wspace': 0.4}, num=2)
    results = {}
    for iter in results_dict_psp.keys():
        for i in range(len(results_dict_psp[iter]["instances"])):
            instance = results_dict_psp[iter]["instances"][i]
            if instance not in results:
                results[instance] = {"orig":[], "current":[]}
            results[instance]["current"].append(results_dict_psp[iter]["costs_times"][i])
            if iter in results_dict_orig:
                try:
                    index_orig = results_dict_orig[iter]["instances"].index(instance)
                    results[instance]["orig"].append(results_dict_orig[iter]["costs_times"][index_orig])
                except ValueError:
                    pass

    for i, instance in enumerate(results.keys()):
        mean, interval, time_points = get_confidence_time(results[instance]["current"], n_points=1000)
        time_points = [s/60 for s in time_points]
        label = labels[modules.index(instance[:3])]
        axes2[i%6,int(i/6)].set_title(label)
        line_psp_no = axes2[i%6,int(i/6)].plot(time_points, mean, label = "current PSP")
        lower_confidence = [x[0] for x in interval]
        upper_confidence = [x[1] for x in interval]
        axes2[i%6,int(i/6)].fill_between(time_points, lower_confidence, upper_confidence, alpha=0.2)

        if results[instance]["orig"]:
            mean, interval, time_points = get_confidence_time(results[instance]["orig"], n_points=1000)
            time_points = [s/60 for s in time_points]
            label = labels[modules.index(instance[:3])]
            axes2[i%6,int(i/6)].set_title(label)
            line_psp_alpha = axes2[i%6,int(i/6)].plot(time_points, mean, label = "original PSP")
            lower_confidence = [x[0] for x in interval]
            upper_confidence = [x[1] for x in interval]
            axes2[i%6,int(i/6)].fill_between(time_points, lower_confidence, upper_confidence, alpha=0.2)
        #axes2[i%6,int(i/6)].legend(loc="upper right")
        axes2[i%6,int(i/6)].set_ylim((0,2))
        axes2[i%6,int(i/6)].set_xlabel("time [min]")
        axes2[i%6,int(i/6)].set_ylabel("cost [1]")
    
    #lines = []
    #legend_texts = []
    #for ax in axes2: 
    #    Line, Label = ax.get_legend_handles_labels() 
    #    # print(Label) 
    #    lines.extend(Line) 
    #    legend_texts.extend(Label) 
    #fig2.legend(lines, legend_texts, loc="bottom right")
    lines, texts = axes2[0,0].get_legend_handles_labels()
    fig2.legend(lines, texts, loc = "lower right")
    print("130 trials for each run (alpha and noKnowledge)")

    axes1.set_xlabel("time [min]", fontsize=14)
    axes1.set_ylabel("learned skills [1]", fontsize=14)
    axes1.set_title("original VS current PSP", fontsize=14)
    axes1.set_xlim((0,55))
    axes1.grid()
    axes1.legend(loc="lower right", fontsize=14)
    plt.show()

def plot_CMAES():
    new_cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088}
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    
    print("\ngetting collective data")
    mean_collective, confidence_collective = get_big_collective_data(["CMAES"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective = [x/60 for x in mean_collective]
    lower_bound_confindece_collective = [x[0]/60 for x in confidence_collective]
    upper_bound_confindece_collective = [x[1]/60 for x in confidence_collective]
    legend_collective = axes1.plot(mean_collective, range(len(mean_collective)), label="collective knowledge sharing (5 agents)")
    axes1.fill_betweenx(range(len(mean_collective)), lower_bound_confindece_collective, upper_bound_confindece_collective, alpha=0.2)
    
    axes1.set_xlabel("time [min]", fontsize=14)
    axes1.set_ylabel("learned skills [1]", fontsize=14)
    axes1.set_title("learn 25 skills | 5 agent collective VS 10 agent collective", fontsize=14)
    axes1.set_xlim((0,700))
    axes1.set_xlim((0,180))
    axes1.grid()
    axes1.legend(loc="lower right", fontsize=14)
    plt.show()

def plot_pitstop_alpha():
    new_cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088}
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    
    print("\ngetting data - collective with 10 agents")
    mean_collective_10, confidence_collective_10 = get_big_collective_data(["10agents_25tasks","collective","ps_alpha_5"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_10 = [x/60 for x in mean_collective_10]
    lower_bound_confindece_collective_10 = [x[0]/60 for x in confidence_collective_10]
    upper_bound_confindece_collective_10 = [x[1]/60 for x in confidence_collective_10]
    legend_collective = axes1.plot(mean_collective_10, range(len(mean_collective_10)), label="collective knowledge sharing (10 agents)")
    axes1.fill_betweenx(range(len(mean_collective_10)), lower_bound_confindece_collective_10, upper_bound_confindece_collective_10, alpha=0.2)
    print("\ngetting data - collective with 10 agents reverse")
    mean_collective_10_re, confidence_collective_10_re = get_big_collective_data(["10agents_25tasks","collective","ps_alpha_5_reverse"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_10_re = [x/60 for x in mean_collective_10_re]
    lower_bound_confindece_collective_10_re = [x[0]/60 for x in confidence_collective_10_re]
    upper_bound_confindece_collective_10_re = [x[1]/60 for x in confidence_collective_10_re]
    legend_collective = axes1.plot(mean_collective_10_re, range(len(mean_collective_10_re)), label="collective knowledge sharing (10 agents) reverse sheduled")
    axes1.fill_betweenx(range(len(mean_collective_10_re)), lower_bound_confindece_collective_10_re, upper_bound_confindece_collective_10_re, alpha=0.2)
    print("\ngetting data - collective with 5 agents")
    mean_collective_5, confidence_collective_5 = get_big_collective_data(["5agents_25tasks","collective"])  # history: ["5agents_25tasks","collective"]
    mean_collective_5 = [x/60 for x in mean_collective_5]
    lower_bound_confindece_collective_5 = [x[0]/60 for x in confidence_collective_5]
    upper_bound_confindece_collective_5 = [x[1]/60 for x in confidence_collective_5]
    legend_collective = axes1.plot(mean_collective_5, range(len(mean_collective_5)), label="collective knowledge sharing (5 agents)")
    axes1.fill_betweenx(range(len(mean_collective_5)), lower_bound_confindece_collective_5, upper_bound_confindece_collective_5, alpha=0.2)
    print("\ngetting data - collective with 6 agents")
    mean_collective_6, confidence_collective_6 = get_big_collective_data(["6agents_25tasks","collective"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_6 = [x/60 for x in mean_collective_6]
    lower_bound_confindece_collective_6 = [x[0]/60 for x in confidence_collective_6]
    upper_bound_confindece_collective_6 = [x[1]/60 for x in confidence_collective_6]
    legend_collective = axes1.plot(mean_collective_6, range(len(mean_collective_6)), label="collective knowledge sharing (6 agents)")
    axes1.fill_betweenx(range(len(mean_collective_6)), lower_bound_confindece_collective_6, upper_bound_confindece_collective_6, alpha=0.2)
    print("\ngetting data - collective with 7 agents")
    mean_collective_7, confidence_collective_7 = get_big_collective_data(["7agents_25tasks","collective"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_7 = [x/60 for x in mean_collective_7]
    lower_bound_confindece_collective_7 = [x[0]/60 for x in confidence_collective_7]
    upper_bound_confindece_collective_7 = [x[1]/60 for x in confidence_collective_7]
    legend_collective = axes1.plot(mean_collective_7, range(len(mean_collective_7)), label="collective knowledge sharing (7 agents)")
    axes1.fill_betweenx(range(len(mean_collective_7)), lower_bound_confindece_collective_7, upper_bound_confindece_collective_7, alpha=0.2)
    print("\ngetting data - collective with 8 agents")
    mean_collective_8, confidence_collective_8 = get_big_collective_data(["8agents_25tasks","collective"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_8 = [x/60 for x in mean_collective_8]
    lower_bound_confindece_collective_8 = [x[0]/60 for x in confidence_collective_8]
    upper_bound_confindece_collective_8 = [x[1]/60 for x in confidence_collective_8]
    legend_collective = axes1.plot(mean_collective_8, range(len(mean_collective_8)), label="collective knowledge sharing (8 agents)")
    axes1.fill_betweenx(range(len(mean_collective_8)), lower_bound_confindece_collective_8, upper_bound_confindece_collective_8, alpha=0.2)
    print("\ngetting data - collective with 9 agents")
    mean_collective_9, confidence_collective_9 = get_big_collective_data(["9agents_25tasks","collective"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_9 = [x/60 for x in mean_collective_9]
    lower_bound_confindece_collective_9 = [x[0]/60 for x in confidence_collective_9]
    upper_bound_confindece_collective_9 = [x[1]/60 for x in confidence_collective_9]
    legend_collective = axes1.plot(mean_collective_9, range(len(mean_collective_9)), label="collective knowledge sharing (9 agents)")
    axes1.fill_betweenx(range(len(mean_collective_9)), lower_bound_confindece_collective_9, upper_bound_confindece_collective_9, alpha=0.2)
    print("\ngetting data - collective with 1 agents")
    mean_collective_1, confidence_collective_1 = get_big_collective_data(["1agents_25tasks","collective"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_1 = [x/60 for x in mean_collective_1]
    lower_bound_confindece_collective_1 = [x[0]/60 for x in confidence_collective_1]
    upper_bound_confindece_collective_1 = [x[1]/60 for x in confidence_collective_1]
    legend_collective = axes1.plot(mean_collective_1, range(len(mean_collective_1)), label="collective knowledge sharing (1 agents)")
    axes1.fill_betweenx(range(len(mean_collective_1)), lower_bound_confindece_collective_1, upper_bound_confindece_collective_1, alpha=0.2)
    print("\ngetting data - collective with 2 agents")
    mean_collective_2, confidence_collective_2 = get_big_collective_data(["2agents_25tasks","collective"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_2 = [x/60 for x in mean_collective_2]
    lower_bound_confindece_collective_2 = [x[0]/60 for x in confidence_collective_2]
    upper_bound_confindece_collective_2 = [x[1]/60 for x in confidence_collective_2]
    legend_collective = axes1.plot(mean_collective_2, range(len(mean_collective_2)), label="collective knowledge sharing (2 agents)")
    axes1.fill_betweenx(range(len(mean_collective_2)), lower_bound_confindece_collective_2, upper_bound_confindece_collective_2, alpha=0.2)
    print("\ngetting data - collective with 3 agents")
    mean_collective_3, confidence_collective_3 = get_big_collective_data(["3agents_25tasks","collective"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_3 = [x/60 for x in mean_collective_3]
    lower_bound_confindece_collective_3 = [x[0]/60 for x in confidence_collective_3]
    upper_bound_confindece_collective_3 = [x[1]/60 for x in confidence_collective_3]
    legend_collective = axes1.plot(mean_collective_3, range(len(mean_collective_3)), label="collective knowledge sharing (3 agents)")
    axes1.fill_betweenx(range(len(mean_collective_3)), lower_bound_confindece_collective_3, upper_bound_confindece_collective_3, alpha=0.2)
    print("\ngetting data - collective with 4 agents")
    mean_collective_4, confidence_collective_4 = get_big_collective_data(["4agents_25tasks","collective"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_4 = [x/60 for x in mean_collective_4]
    lower_bound_confindece_collective_4 = [x[0]/60 for x in confidence_collective_4]
    upper_bound_confindece_collective_4 = [x[1]/60 for x in confidence_collective_4]
    legend_collective = axes1.plot(mean_collective_4, range(len(mean_collective_4)), label="collective knowledge sharing (4 agents)")
    axes1.fill_betweenx(range(len(mean_collective_4)), lower_bound_confindece_collective_4, upper_bound_confindece_collective_4, alpha=0.2)
    
    #print(["\n5agents_25tasks_rearanged", "collective"])
    #mean_collective_re, confidence_collective_re = get_big_collective_data(["5agents_25tasks_rearanged", "collective"])  # history: ["5agents_25tasks_rearanged", "collective"]
    #mean_collective_re = [x/60 for x in mean_collective_re]
    #lower_bound_confindece_collective_re = [x[0]/60 for x in confidence_collective_re]
    #upper_bound_confindece_collective_re = [x[1]/60 for x in confidence_collective_re]
    #legend_collective_re = axes1.plot(mean_collective_re, range(len(mean_collective_re)), label="collective knowledge sharing (5 agents, optimised sequence)")
    #axes1.fill_betweenx(range(len(mean_collective_re)), lower_bound_confindece_collective_re, upper_bound_confindece_collective_re, alpha=0.2)
    

    axes1.set_xlabel("time [min]", fontsize=14)
    axes1.set_ylabel("learned skills [1]", fontsize=14)
    axes1.set_title("learn 25 skills | 5 agent collective VS 10 agent collective", fontsize=14)
    axes1.set_xlim((0,700))
    axes1.set_xlim((0,180))
    axes1.grid()
    axes1.legend(loc="lower right", fontsize=14)
    plt.show(block=False)

    print("total learning time comparison")
    fig2, axes2 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2)
    y = []
    var = []
    for i,(time,confidence) in enumerate(zip([mean_collective_1,mean_collective_2,mean_collective_3,mean_collective_4,mean_collective_5,
    mean_collective_6,mean_collective_7,mean_collective_8,mean_collective_9,mean_collective_10], [
        (lower_bound_confindece_collective_1[-1], upper_bound_confindece_collective_1[-1]),
        (lower_bound_confindece_collective_2[-1], upper_bound_confindece_collective_2[-1]),
        (lower_bound_confindece_collective_3[-1], upper_bound_confindece_collective_3[-1]),
        (lower_bound_confindece_collective_4[-1], upper_bound_confindece_collective_4[-1]),
        (lower_bound_confindece_collective_5[-1], upper_bound_confindece_collective_5[-1]),
        (lower_bound_confindece_collective_6[-1], upper_bound_confindece_collective_6[-1]),
        (lower_bound_confindece_collective_7[-1], upper_bound_confindece_collective_7[-1]),
        (lower_bound_confindece_collective_8[-1], upper_bound_confindece_collective_8[-1]),
        (lower_bound_confindece_collective_9[-1], upper_bound_confindece_collective_9[-1]),
        (lower_bound_confindece_collective_10[-1], upper_bound_confindece_collective_10[-1]),
        
    ])):
        y.append(time[-1]*i)
        var.append([v + (time[-1]*(i-1) ) for v in confidence])
        #var.append(confidence)
    print(var)
    axes2.plot(range(1,11),y,label="agent dependent total learning time (25 tasks)")
    axes2.fill_between(range(1,11), [v[0] for v in var], [v[1] for v in var], alpha=0.2)
    #axes2.set_ylim(0,200)
    axes2.set_ylabel("learning time [min] * agent")
    axes2.set_xlabel("number of agents")
    axes2.set_title("collective with 25 tasks")
    axes2.grid()
    axes2.legend(loc="upper right", fontsize=14)
    plt.show(block=False)


def plot_alphaX():
    new_cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088}
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    
    print("\ngetting data - collective with 10 agents")
    mean_collective_10, confidence_collective_10 = get_big_collective_data(["10agents_25tasks","collective","ps_alpha_5"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_10 = [x/60 for x in mean_collective_10]
    lower_bound_confindece_collective_10 = [x[0]/60 for x in confidence_collective_10]
    upper_bound_confindece_collective_10 = [x[1]/60 for x in confidence_collective_10]
    legend_collective = axes1.plot(mean_collective_10, range(len(mean_collective_10)), label="collective knowledge sharing (10 agents)")
    axes1.fill_betweenx(range(len(mean_collective_10)), lower_bound_confindece_collective_10, upper_bound_confindece_collective_10, alpha=0.2)
    print("\ngetting data - collective with 10 agents reverse")
    mean_collective_10_re, confidence_collective_10_re = get_big_collective_data(["10agents_25tasks","collective","ps_alpha_5_reverse"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_10_re = [x/60 for x in mean_collective_10_re]
    lower_bound_confindece_collective_10_re = [x[0]/60 for x in confidence_collective_10_re]
    upper_bound_confindece_collective_10_re = [x[1]/60 for x in confidence_collective_10_re]
    legend_collective = axes1.plot(mean_collective_10_re, range(len(mean_collective_10_re)), label="collective knowledge sharing (10 agents) reverse sheduled")
    axes1.fill_betweenx(range(len(mean_collective_10_re)), lower_bound_confindece_collective_10_re, upper_bound_confindece_collective_10_re, alpha=0.2)
    print("\ngetting data - collective with 5 agents")
    mean_collective_5, confidence_collective_5 = get_big_collective_data(["5agents_25tasks","collective"])  # history: ["5agents_25tasks","collective"]
    mean_collective_5 = [x/60 for x in mean_collective_5]
    lower_bound_confindece_collective_5 = [x[0]/60 for x in confidence_collective_5]
    upper_bound_confindece_collective_5 = [x[1]/60 for x in confidence_collective_5]
    legend_collective = axes1.plot(mean_collective_5, range(len(mean_collective_5)), label="collective knowledge sharing (5 agents)")
    axes1.fill_betweenx(range(len(mean_collective_5)), lower_bound_confindece_collective_5, upper_bound_confindece_collective_5, alpha=0.2)
    print("\ngetting data - collective with 6 agents")
    mean_collective_6, confidence_collective_6 = get_big_collective_data(["6agents_25tasks","collective","ps_alpha_var"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_6 = [x/60 for x in mean_collective_6]
    lower_bound_confindece_collective_6 = [x[0]/60 for x in confidence_collective_6]
    upper_bound_confindece_collective_6 = [x[1]/60 for x in confidence_collective_6]
    legend_collective = axes1.plot(mean_collective_6, range(len(mean_collective_6)), label="collective knowledge sharing (6 agents)")
    axes1.fill_betweenx(range(len(mean_collective_6)), lower_bound_confindece_collective_6, upper_bound_confindece_collective_6, alpha=0.2)
    print("\ngetting data - collective with 7 agents")
    mean_collective_7, confidence_collective_7 = get_big_collective_data(["7agents_25tasks","collective","ps_alpha_var"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_7 = [x/60 for x in mean_collective_7]
    lower_bound_confindece_collective_7 = [x[0]/60 for x in confidence_collective_7]
    upper_bound_confindece_collective_7 = [x[1]/60 for x in confidence_collective_7]
    legend_collective = axes1.plot(mean_collective_7, range(len(mean_collective_7)), label="collective knowledge sharing (7 agents)")
    axes1.fill_betweenx(range(len(mean_collective_7)), lower_bound_confindece_collective_7, upper_bound_confindece_collective_7, alpha=0.2)
    print("\ngetting data - collective with 8 agents")
    mean_collective_8, confidence_collective_8 = get_big_collective_data(["8agents_25tasks","collective"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_8 = [x/60 for x in mean_collective_8]
    lower_bound_confindece_collective_8 = [x[0]/60 for x in confidence_collective_8]
    upper_bound_confindece_collective_8 = [x[1]/60 for x in confidence_collective_8]
    legend_collective = axes1.plot(mean_collective_8, range(len(mean_collective_8)), label="collective knowledge sharing (8 agents)")
    axes1.fill_betweenx(range(len(mean_collective_8)), lower_bound_confindece_collective_8, upper_bound_confindece_collective_8, alpha=0.2)
    print("\ngetting data - collective with 9 agents")
    mean_collective_9, confidence_collective_9 = get_big_collective_data(["9agents_25tasks","collective","ps_alpha_var"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_9 = [x/60 for x in mean_collective_9]
    lower_bound_confindece_collective_9 = [x[0]/60 for x in confidence_collective_9]
    upper_bound_confindece_collective_9 = [x[1]/60 for x in confidence_collective_9]
    legend_collective = axes1.plot(mean_collective_9, range(len(mean_collective_9)), label="collective knowledge sharing (9 agents)")
    axes1.fill_betweenx(range(len(mean_collective_9)), lower_bound_confindece_collective_9, upper_bound_confindece_collective_9, alpha=0.2)
    
    #print(["\n5agents_25tasks_rearanged", "collective"])
    #mean_collective_re, confidence_collective_re = get_big_collective_data(["5agents_25tasks_rearanged", "collective"])  # history: ["5agents_25tasks_rearanged", "collective"]
    #mean_collective_re = [x/60 for x in mean_collective_re]
    #lower_bound_confindece_collective_re = [x[0]/60 for x in confidence_collective_re]
    #upper_bound_confindece_collective_re = [x[1]/60 for x in confidence_collective_re]
    #legend_collective_re = axes1.plot(mean_collective_re, range(len(mean_collective_re)), label="collective knowledge sharing (5 agents, optimised sequence)")
    #axes1.fill_betweenx(range(len(mean_collective_re)), lower_bound_confindece_collective_re, upper_bound_confindece_collective_re, alpha=0.2)
    

    axes1.set_xlabel("time [min]", fontsize=14)
    axes1.set_ylabel("learned skills [1]", fontsize=14)
    axes1.set_title("learn 25 skills | 5 agent collective VS 10 agent collective", fontsize=14)
    axes1.set_xlim((0,700))
    axes1.set_xlim((0,180))
    axes1.grid()
    axes1.legend(loc="lower right", fontsize=14)
    plt.show(block=False)

    print("total learning time comparison")
    fig2, axes2 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2)
    y = []
    for time in [mean_collective_5,mean_collective_6,mean_collective_7,mean_collective_8,mean_collective_9,mean_collective_10]:
        y.append(time[-1])
    
    for i in range(6):
        y[i] = y[i] * (i+5)
        
    # axes1.fill_betweenx(range(5.9), lower_bound_confindece_collective_9, upper_bound_confindece_collective_9, alpha=0.2)
    
    axes2.plot(range(5,11),y,label="agent dependent total learning time (25 tasks)")
    axes2.set_ylabel("total robot learning time [min]")
    axes2.set_xlabel("number of agents")
    axes2.set_title("collective with 25 tasks")
    axes2.grid()
    axes2.legend(loc="upper right", fontsize=14)
    # plt.show(block=False)
    plt.savefig("alphaX_010224")

def plot_pitstop_bravo():
    new_cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088}
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    
    print("\ngetting data - collective 0 request rate")
    mean_collective_rr0, confidence_collective_rr0 = get_big_collective_data(["ReqR0","collective","ps_bravo_4"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr0_2, confidence_collective_rr0_2 = get_big_collective_data(["ReqR0","collective","ps_bravo_5"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr0.extend(mean_collective_rr0_2)
    confidence_collective_rr0.extend(confidence_collective_rr0_2)
    mean_collective_rr0 = [x/60 for x in mean_collective_rr0]
    lower_bound_confindece_collective_rr0 = [x[0]/60 for x in confidence_collective_rr0]
    upper_bound_confindece_collective_rr0 = [x[1]/60 for x in confidence_collective_rr0]
    legend_collective = axes1.plot(mean_collective_rr0, range(len(mean_collective_rr0)), label="Request Rate 0%")
    axes1.fill_betweenx(range(len(mean_collective_rr0)), lower_bound_confindece_collective_rr0, upper_bound_confindece_collective_rr0, alpha=0.2)
    print("\ngetting data - collective 0.2 request rate")
    mean_collective_rr02, confidence_collective_rr02 = get_big_collective_data(["ReqR0.2","collective","ps_bravo_4"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr02_2, confidence_collective_rr02_2 = get_big_collective_data(["ReqR0.2","collective","ps_bravo_5"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr02.extend(mean_collective_rr02_2)
    confidence_collective_rr02.extend(confidence_collective_rr02_2)
    mean_collective_rr02 = [x/60 for x in mean_collective_rr02]
    lower_bound_confindece_collective_rr02 = [x[0]/60 for x in confidence_collective_rr02]
    upper_bound_confindece_collective_rr02 = [x[1]/60 for x in confidence_collective_rr02]
    legend_collective = axes1.plot(mean_collective_rr02, range(len(mean_collective_rr02)), label="Request Rate 20%")
    axes1.fill_betweenx(range(len(mean_collective_rr02)), lower_bound_confindece_collective_rr02, upper_bound_confindece_collective_rr02, alpha=0.2)
    print("\ngetting data - collective 0.4 request rate")
    mean_collective_rr04, confidence_collective_rr04 = get_big_collective_data(["5agents_25tasks","collective"])  # history: ["5agents_25tasks","collective"]
    #mean_collective_rr04_2, confidence_collective_rr04_2 = get_big_collective_data(["ReqR0","collective","ps_bravo_5"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    #mean_collective_rr04.extend(mean_collective_rr04_2)
    #confidence_collective_rr04.extend(confidence_collective_rr04_2)
    mean_collective_rr04 = [x/60 for x in mean_collective_rr04]
    lower_bound_confindece_collective_rr04 = [x[0]/60 for x in confidence_collective_rr04]
    upper_bound_confindece_collective_rr04 = [x[1]/60 for x in confidence_collective_rr04]
    legend_collective = axes1.plot(mean_collective_rr04, range(len(mean_collective_rr04)), label="Request Rate 40%")
    axes1.fill_betweenx(range(len(mean_collective_rr04)), lower_bound_confindece_collective_rr04, upper_bound_confindece_collective_rr04, alpha=0.2)
    print("\ngetting data - collective 0.6 request rate")
    mean_collective_rr06, confidence_collective_rr06 = get_big_collective_data(["ReqR0.6","collective","ps_bravo_4"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr06_2, confidence_collective_rr06_2 = get_big_collective_data(["ReqR0.6","collective","ps_bravo_5"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr06.extend(mean_collective_rr06_2)
    confidence_collective_rr06.extend(confidence_collective_rr06_2)
    mean_collective_rr06 = [x/60 for x in mean_collective_rr06]
    lower_bound_confindece_collective_rr06 = [x[0]/60 for x in confidence_collective_rr06]
    upper_bound_confindece_collective_rr06 = [x[1]/60 for x in confidence_collective_rr06]
    legend_collective = axes1.plot(mean_collective_rr06, range(len(mean_collective_rr06)), label="Request Rate 60%")
    axes1.fill_betweenx(range(len(mean_collective_rr06)), lower_bound_confindece_collective_rr06, upper_bound_confindece_collective_rr06, alpha=0.2)
    print("\ngetting data - collective 0.8 request rate")
    mean_collective_rr08, confidence_collective_rr08 = get_big_collective_data(["ReqR0.8","collective","ps_bravo_4"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr08_2, confidence_collective_rr08_2 = get_big_collective_data(["ReqR0.8","collective","ps_bravo_5"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr08.extend(mean_collective_rr08_2)
    confidence_collective_rr08.extend(confidence_collective_rr08_2)
    mean_collective_rr08 = [x/60 for x in mean_collective_rr08]
    lower_bound_confindece_collective_rr08 = [x[0]/60 for x in confidence_collective_rr08]
    upper_bound_confindece_collective_rr08 = [x[1]/60 for x in confidence_collective_rr08]
    legend_collective = axes1.plot(mean_collective_rr08, range(len(mean_collective_rr08)), label="Request Rate 80%")
    axes1.fill_betweenx(range(len(mean_collective_rr08)), lower_bound_confindece_collective_rr08, upper_bound_confindece_collective_rr08, alpha=0.2)
    print("\ngetting data - collective 100% request rate")
    mean_collective_rr1, confidence_collective_rr1 = get_big_collective_data(["ReqR1","collective","ps_bravo_4"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr1_2, confidence_collective_rr1_2 = get_big_collective_data(["ReqR1","collective","ps_bravo_5"],cutoff=new_cutoff)  # history: ["5agents_25tasks","collective"]
    mean_collective_rr1.extend(mean_collective_rr1_2)
    confidence_collective_rr1.extend(confidence_collective_rr1_2)
    mean_collective_rr1 = [x/60 for x in mean_collective_rr1]
    lower_bound_confindece_collective_rr1 = [x[0]/60 for x in confidence_collective_rr1]
    upper_bound_confindece_collective_rr1 = [x[1]/60 for x in confidence_collective_rr1]
    legend_collective = axes1.plot(mean_collective_rr1, range(len(mean_collective_rr1)), label="Request Rate 100%")
    axes1.fill_betweenx(range(len(mean_collective_rr1)), lower_bound_confindece_collective_rr1, upper_bound_confindece_collective_rr1, alpha=0.2)
        
    axes1.set_xlabel("time [min]", fontsize=14)
    axes1.set_ylabel("learned skills [1]", fontsize=14)
    axes1.set_title("learn 25 skills | 5 agent collective: investigate Request Rates", fontsize=14)
    axes1.set_xlim((0,700))
    axes1.set_xlim((0,180))
    axes1.grid()
    axes1.legend(loc="lower right", fontsize=14)
    plt.show(block=False)

    print("total learning time comparison")
    fig2, axes2 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2)
    y = []
    var = []
    for i,(time,confidence) in enumerate(zip([mean_collective_rr0,mean_collective_rr02,mean_collective_rr04,mean_collective_rr06,mean_collective_rr08,
    mean_collective_rr1], [
        (lower_bound_confindece_collective_rr0[-1], upper_bound_confindece_collective_rr0[-1]),
        (lower_bound_confindece_collective_rr02[-1], upper_bound_confindece_collective_rr02[-1]),
        (lower_bound_confindece_collective_rr04[-1], upper_bound_confindece_collective_rr04[-1]),
        (lower_bound_confindece_collective_rr06[-1], upper_bound_confindece_collective_rr06[-1]),
        (lower_bound_confindece_collective_rr08[-1], upper_bound_confindece_collective_rr08[-1]),
        (lower_bound_confindece_collective_rr1[-1], upper_bound_confindece_collective_rr1[-1]),

        
    ])):
        y.append(time[-1])
        var.append([v for v in confidence])
        #var.append(confidence)
    print(var)
    axes2.plot(range(len(y)),y,label="requets dependent total learning time (25 tasks)")
    axes2.fill_between(range(len(var)), [v[0] for v in var], [v[1] for v in var], alpha=0.2)
    axes2.set_xticks(range(len(y)),labels=['0%','20%','40%','60%','80%','100%',])
    #axes2.set_ylim(0,200)
    axes2.set_ylabel("learning time [min]")
    axes2.set_xlabel("Request Rate in [%]")
    axes2.set_title("learn 25 skills | 5 agent collective: investigate Request Rates")
    axes2.grid()
    axes2.legend(loc="upper right", fontsize=14)
    plt.show(block=False)

def video_plot_big_collective():
    def plot_frame(i, collective, isolated_single):
        reduce_factor = 1#00
        if (i-1)*reduce_factor <= (isolated_single[-1] - collective[-1])*60:
            data = [x for x in isolated_single if x*60<=i*reduce_factor]
            graph_isolated.set_data(data, range(len(data)))
        else:
            data = [x for x in isolated_single if x*60<=i*reduce_factor]
            graph_isolated.set_data(data, range(len(data)))
            #i=int((i*reduce_factor - ((isolated_single[-1] - collective[-1])*60) / reduce_factor))
            data = [x for x in collective if (x +(isolated_single[-1] - collective[-1]))*60<i*reduce_factor]
            graph_collective.set_data(data, range(len(data)))

    # Create a figure and axis
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1,figsize=(16, 12))
    axes1.set_xlabel("time [min]", fontsize=14)
    axes1.set_ylabel("learned skills [1]", fontsize=14)
    axes1.set_title("5 agents collective | 1 agent isolated", fontsize=14)
    axes1.set_xlim((0,575))
    axes1.set_ylim((0,25))
    axes1.grid()
    graph_isolated, = plt.plot([], [], color="green",label="isolated single")
    graph_collective, = plt.plot([], [], color="blue",label="collective knowledge sharing")
    axes1.legend(loc="lower right", fontsize=14)

    print("\ngetting collective data")
    mean_collective, confidence_collective = get_big_collective_data(["5agents_25tasks","collective", "n30"])
    mean_collective = [x/60 for x in mean_collective]

    print("\ngetting single isolated data")
    mean_isolated_single, confidence_isolated_single = get_big_collective_data(["5agents_25tasks_local","isolated_local_noFastPipeline", "n30"], single_agent=True)
    mean_isolated_single = [x/60 for x in mean_isolated_single]

    total_time = mean_isolated_single[-1]  #in minutes
    print("total_time ",total_time)
    num_frames =  int(total_time*60)+1  # Number of frames with framerate 1
    num_frames += 10  #add 10 sec to the end 
    #num_frames  = int(num_frames/100)
    print("total frames: ", num_frames, "  in min: ",num_frames/60)
    print("collective: ",mean_collective, len(mean_collective))
    print("isolated: ",mean_isolated_single)
    input("continue?")
    ani = FuncAnimation(fig1, plot_frame, frames=num_frames, fargs=(mean_collective, mean_isolated_single), repeat=False, interval=0.1)

    # Save the animation as a video (replace 'animation.mp4' with your desired filename)
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=1, bitrate=1800)
    ani.save("collective_isolated"+'.mp4', writer=writer,  progress_callback = lambda i, n: print(f'Progress {i/n}'))


#[x for sublist in listoflists for x in sublist]
#[x for sublist in listoflistsoflists for subsublist in sublist for x in subsublist]
    
def plot_transfer_map():
    tags_list = [["10agents_25tasks","collective","ps_alpha_5_reverse","n1"],["10agents_25tasks","collective","ps_alpha_5","n1"]]
    modules = list_block_1 + list_block_2 + list_U
    transfer_matrix = np.ones((len(modules),len(modules)))*float("inf")  #init transfer matrix
    for m_index, m in enumerate(modules):
        results = []
        for tags in tags_list:
            results.extend(get_multiple_experiment_data("collective-"+m+".rsi.ei.tum.de","insertion", filter={"meta.tags":tags}))
        for result in results:
            for trial in result.trials:
                if trial["q_metric"]["success"] is False:
                    continue
                transfer_index = None
                try:
                    external = eval(trial["external"])["skill_instance"][:3]
                    transfer_index = modules.index(external)
                    print(external, transfer_index)
                except TypeError:
                    transfer_index = m_index
                if trial["q_metric"]["final_cost"] < transfer_matrix[m_index][transfer_index]:
                    transfer_matrix[m_index][transfer_index] = trial["q_metric"]["final_cost"]
    fig, ax = plt.subplots(figsize=(16, 12))
    color_list = ["#E7F1E7","#D4E6D4","#BDD7BD","#A7CBA7","#8DBB8D","#78AE78","#5E9E5E","#479147","#308030","#197519","#016701"]
    color_list.reverse()
    cmap = colors.ListedColormap(color_list)
    bounds = [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
    # bounds = list(range(11))
    norm = colors.BoundaryNorm(bounds, cmap.N)    # labels = ["task"+str(i) for i in range(1,26)]
    labels = ["IEC(C7)", "Triangle-1", "Hexagon-1", "USB-1", "Triangle-2", "Cylinder-1", "Key-1", "Plug(type F)-1", "Audio Jack\n(3.5mm)", "IEC(C13)", "Cylinder-2", "Hexagon-2", "HDMI-1", "Key-2", "Cylinder-3", "Square-1", "Hexagon-3", "Square-2", "Audio jack\n(6.35mm)", "USB-2", "Plug(type C)", "Key-3", "Plug(type F)-2", "HDMI-2", "Key-4"]

    plt.clf()
    # c = sns.color_palette("light:#006600", as_cmap=True)
    ax = sns.heatmap(transfer_matrix, linewidth=0.5, cmap=cmap, norm=norm, annot=True, fmt=".2f") #fmt="g"

    ax.set_xticklabels(labels, rotation=90)    
    ax.set_yticklabels(labels, rotation=0)  
    cbar = ax.collections[0].colorbar
    cbar.set_ticks(bounds)
    # ax.set_yticks([])  # Remove y labels
    # plt.title("Collective Learning Process")

    ax.set_title(f'Collective Learning Process')
    plt.show(block=False)
        


def plot_collective_experiment_time():
    import time

    tags = ["collective_learning_alt"]

    robots = {  "collective-panda-prime.local": ["key_door"],
                "collective-panda-002.local": ["key_abus_e30"],
                "collective-panda-003.local": ["key_padlock","key_2"],
                "collective-panda-004.local": ["cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_50", "cylinder_60"],
                "collective-panda-008.local": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
             }
    if tags[0] == "collective_learning_alt":
        robots = {  "collective-panda-prime": ["key_door"],
                    "collective-panda-002": ["key_abus_e30"],
                    "collective-panda-003": ["key_padlock", "key_2"], #
                    "collective-panda-004": [ "cylinder_30","cylinder_60", "cylinder_40", "cylinder_10", "cylinder_20"  ,"cylinder_50"], #, "cylinder_20"  ,"cylinder_50"], #  
                    "collective-panda-008": [ "HDMI_plug", "key_padlock_2", "key_hatch", "key_old"] # 
                }
    # cutoff = {  "key_door":0.25,
    #             "key_abus_e30": 0.25,
    #             "key_padlock": 0.25,
    #             "key_2": 0.25,
    #             "cylinder_40": 0.25,
    #             "cylinder_10": 0.3,
    #             "cylinder_20": 0.25,
    #             "cylinder_30": 0.35,
    #             "cylinder_50": 0.28,
    #             "cylinder_60": 0.5,
    #             "HDMI_plug": 0.3,
    #             "key_padlock_2": 0.25,
    #             "key_hatch": 0.25,
    #             "key_old": 0.25
    #             }
    cutoff = {  "key_door":0.25,
                "key_abus_e30": 0.25,
                "key_padlock": 0.25,
                "key_2": 0.25,
                "cylinder_40": 0.45,
                "cylinder_10": 0.5,
                "cylinder_20": 0.35,
                "cylinder_30": 0.4,
                "cylinder_50": 0.35,
                "cylinder_60": 0.55,
                "HDMI_plug": 0.3,
                "key_padlock_2": 0.25,
                "key_hatch": 0.25,
                "key_old": 0.25
                }
    n_tasks = sum([len(tasks) for tasks in robots.values()])
    p = DataProcessor()
    experiments = ["collective_experiment"]
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    legend_handles1 = []
    legend_handles2 = []

    fig1, axes1 = plt.subplots(n_tasks, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    fig2, axes2 = plt.subplots(len(robots), 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2)
    count = 0
    robot_count = 0
    robot_addr = list(robots.keys())
    count_trials_overall = []
    for r in range(len(robot_addr)):
        task_count = 0
        title=False
        last_time = False
        for e in robots[robot_addr[r]]:
            filters = []
            filters.extend(tags)
            filters.append(e)
            print("tags = ", filters)

            results = get_multiple_experiment_data(robot_addr[r], "insertion", filter={"meta.tags": filters})
            indexes2pop = []
            tag_set = set()
            for i in range(len(results)):
                if len(results[i].costs) < 9:
                    indexes2pop.append(i)
                    continue
                if results[i] in tag_set:
                    indexes2pop.append(i)
                tag_set.add(str(results[i].tags))
            if indexes2pop:
                indexes2pop.reverse()
                for i in indexes2pop:
                    results.pop(i)

            if not last_time:
                t_0 = results[0].starting_time
                for res in results:
                    if t_0 > res.starting_time:
                        t_0 = res.starting_time
                    print("t_0= ",t_0, "  starting_time=",res.starting_time)
            else:
                t_0 = last_time
            # monocally decreasing cost:
            mean_cost, cost_confidence, mean_time, time_confindence, _, cutoff_index = p.get_average_cost_over_timestemp(results, 130,cutoff=cutoff[e])
            #mean_cost, cost_confidence = p.get_average_cost_over_time(results, 130, True, None, "all")
            #plot simple decreasing cost for every task
           # cutoff_index = None
           # for i in range(len(mean_cost)):
           #     if mean_cost[i] < cutoff[e] and cutoff_index == None:
           #         cutoff_index = i
            print(cutoff_index)
            if cutoff_index<10:
                cutoff_index = 10
            mean_cost = mean_cost[:cutoff_index]
            cost_confidence = cost_confidence[:cutoff_index]
            mean_time = mean_time[:cutoff_index]
            count_trials_overall.append(len(mean_cost))
            print("mean_cost",len(mean_cost),"\nmean_time", len(mean_time))
            axes1[count].fill_between(np.linspace(1, len(mean_cost), len(mean_cost)), mean_cost - cost_confidence, mean_cost + cost_confidence, alpha=0.2, color=colors[0])
            legend_handle1, = axes1[count].plot([i+1 for i in range(len(mean_cost))], mean_cost, linewidth=2, color=colors[0], label=e)
            legend_handles1.append(legend_handle1)

            axes1[count].set_ylim(0, 2.4)
            axes1[count].set_xlim(1, len(mean_cost))
            axes1[count].grid()
            axes1[count].tick_params(axis="both", which="both", length=0)
            xticks = [i*10 for i in range(1,(int(len(mean_cost)/10)) +1)]
            xticks.insert(0,1)
            axes1[count].set_xticks(xticks)
            axes1[count].set_title(results[0].tags[1], y=1.0, pad=-14)
            axes1[count].set_xlabel("Trial [1]")
            if count == 0:
                axes1[count].set_ylabel("Cost [1]")
                axes1[count].legend(legend_handles1, tags, loc='upper right')#, experiments)
            
            #plot tasks by time they were carried out
            mean_time = [delta_time + t_0 + 10 for delta_time in mean_time]  # add starting time
            axes2[robot_count].fill_between(mean_time, mean_cost-cost_confidence,mean_cost+cost_confidence, alpha=0.2, color=colors[task_count])
            legend_handle2, = axes2[robot_count].plot(mean_time, mean_cost, linewidth=2, color=colors[task_count], label=e)
            legend_handles2.append(legend_handle2)
            print(mean_cost)
            index= next(x for x in range(len(mean_cost)) if mean_cost[x]<=np.mean(mean_cost))
            if e == "key_padlock_2":
                #texthandle = axes2[robot_count].text(mean_time[0]+100,1.5,"xi="+str(len(mean_cost)))
                axes2[robot_count].annotate("xi="+str(len(mean_cost)), xy=(mean_time[index],mean_cost[index]), xytext=(mean_time[0]+100,1.5),arrowprops=dict(facecolor=colors[task_count], shrink=0.05),)
            elif e == "key_hatch":
                #texthandle = axes2[robot_count].text(mean_time[0]+200,1,"xi="+str(len(mean_cost)))
                axes2[robot_count].annotate("xi="+str(len(mean_cost)), xy=(mean_time[index],mean_cost[index]), xytext=(mean_time[0]+200,1),arrowprops=dict(facecolor=colors[task_count], shrink=0.05),)
            elif e == "key_old":
                #texthandle = axes2[robot_count].text(mean_time[0]+300,0.5,"xi="+str(len(mean_cost)))
                axes2[robot_count].annotate("xi="+str(len(mean_cost)), xy=(mean_time[index],mean_cost[index]), xytext=(mean_time[0]+300,0.5),arrowprops=dict(facecolor=colors[task_count], shrink=0.05),)
            elif e == "key_padlock":
                #texthandle = axes2[robot_count].text(mean_time[0]+100,1.5,"xi="+str(len(mean_cost)))
                axes2[robot_count].annotate("xi="+str(len(mean_cost)), xy=(mean_time[index],mean_cost[index]), xytext=(mean_time[0]+100,1.5),arrowprops=dict(facecolor=colors[task_count], shrink=0.05),)
            elif e == "key_2":
                #texthandle = axes2[robot_count].text(mean_time[0]+200,1,"xi="+str(len(mean_cost)))
                axes2[robot_count].annotate("xi="+str(len(mean_cost)), xy=(mean_time[index],mean_cost[index]), xytext=(mean_time[0]+200,1),arrowprops=dict(facecolor=colors[task_count], shrink=0.05),)
            else:
                #texthandle = axes2[robot_count].text(mean_time[0],1,"xi="+str(len(mean_cost)))
                axes2[robot_count].annotate("xi="+str(len(mean_cost)), xy=(mean_time[index],mean_cost[index]) )
            axes2[robot_count].set_ylim(0, 2.4)
            #axes2[robot_count].set_xlim(1, len(mean_cost))
            if not title:
                axes2[robot_count].grid("on")
                axes2[robot_count].set_title(robot_addr[r], y=1.0, pad=-14)
                axes2[robot_count].set_xlabel("time")
                title=True     
            last_time = mean_time[-1] # results[0].starting_time + results[0].total_time
            task_count += 1
            count += 1
        axes2[robot_count].legend(loc='upper right')#, experiments)
        robot_count += 1

    fig1.tight_layout()
    fig2.tight_layout()
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    print("trials overall = ",sum(count_trials_overall))
    plt.show()

#######

def plot_collective_experiment(tags = "collective_learning_04_alt"):
    #tags = ["collective_learning_04_alt"]
    #tags = ["collective_learning_04_ext_alt"]
    ##tags = ["collective_learning_bugfix_alt"]
    ##tags = ["collective_learning_alt"]
    #tags = ["collective_learning_parallel"]
    ##tags = ["collective_learning"]

    #default, collective_learning_04_alt
    robots = {  "collective-panda-prime.local": ["key_door"],
                "collective-panda-002.local": ["key_abus_e30"],
                "collective-panda-003.local": ["key_padlock","key_2"],
                "collective-panda-004.local": ["cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_50", "cylinder_60"], #
                "collective-panda-008.local": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
             }
    if tags[0] == "collective_learning_alt" or tags[0] == "collective_learning_parallel":
        robots = {  "collective-panda-prime": ["key_door"],
                    "collective-panda-002": ["key_abus_e30"],
                    "collective-panda-003": ["key_padlock", "key_2"], #
                    "collective-panda-004": [ "cylinder_30","cylinder_60", "cylinder_40", "cylinder_10", "cylinder_20"  ,"cylinder_50"], #
                    "collective-panda-008": [ "HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
        }
    if tags[0] == "collective_learning_04_ext_alt":
        robots = {  "collective-panda-prime": ["key_door"],
                    "collective-panda-002": ["key_abus_e30"],
                    "collective-panda-003": ["key_padlock", "key_2"], #
                    "collective-panda-004": [ "cylinder_40", "cylinder_20"  ,"cylinder_60"], #
                    "collective-panda-008": [ "HDMI_plug", "key_padlock_2", "key_hatch", "key_old"],
                    "collective-panda-005": ["cylinder_30","cylinder_10","cylinder_50"]
             }
    if tags[0] == "collective_learning_bugfix":
        robots = {  "collective-panda-prime.local": ["key_door"],
                "collective-panda-002.local": ["key_abus_e30"],
                "collective-panda-003.local": ["key_padlock","key_2"],
                "collective-panda-004.local": ["cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_60"], #, "cylinder_50"
                "collective-panda-008.local": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
             }
    if tags[0] == "collective_learning_bugfix_alt":
        robots = {  "collective-panda-prime.local": ["key_door"],
                "collective-panda-002.local": ["key_abus_e30"],
                "collective-panda-003.local": ["key_padlock","key_2"],
                "collective-panda-004.local": [ "cylinder_30","cylinder_60", "cylinder_40", "cylinder_10", "cylinder_20"], #, "cylinder_50"
                "collective-panda-008.local": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
             }
    cutoff = {  "key_door":0.25,
                "key_abus_e30": 0.25,
                "key_padlock": 0.25,
                "key_2": 0.25,
                "cylinder_40": 0.45,
                "cylinder_10": 0.5,
                "cylinder_20": 0.35,
                "cylinder_30": 0.4,
                "cylinder_50": 0.35,
                "cylinder_60": 0.55,
                "HDMI_plug": 0.3,
                "key_padlock_2": 0.25,
                "key_hatch": 0.25,
                "key_old": 0.25
                }
    #for key in cutoff.keys():
    #    cutoff[key] = cutoff[key] * 1.5
    

    robot_addr = list(robots.keys())
    n_tasks = sum([len(tasks) for tasks in robots.values()])
    p = DataProcessor()
    experiments = ["collective_experiment"]
    colors = ["blue", "red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    legend_handles1 = []
    legend_handles2 = []

    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    count = 0
    robot_count = 0
    
    count_trials_overall = []
    xticks = []
    xticks_labels = []
    count_agents = 0
    count_bars = 0
    average_experiment_times = []
    time_robots = []
    agent_task_times = []
    agent_task_times_var = []
    for r in range(len(robot_addr)):
        task_count = 0
        title=False
        last_time = False
        robot_time = []
        agent_task_time = []
        agent_task_time_var = []
        for e in robots[robot_addr[r]]:
            filters = []
            filters.extend(tags)
            filters.append(e)
            print("tags = ", filters)

            results = get_multiple_experiment_data(robot_addr[r], "insertion", filter={"meta.tags": filters})
            indexes2pop = []
            tag_set = set()
            average_time = 0  # for 1 experiment
            for i in range(len(results)):
                #if i < 4:  #  just for extended experiment bcause cylinder 10 was not working for the first 4 runs
                #    indexes2pop.append(i)
                #    continue
                if len(results[i].costs) < 9:
                    indexes2pop.append(i)
                    continue
                if results[i] in tag_set:
                    indexes2pop.append(i)
                tag_set.add(str(results[i].tags))
                average_time += results[i].total_time
            if indexes2pop:
                indexes2pop.reverse()
                for i in indexes2pop:
                    results.pop(i)
            average_time, time_var = p.get_average_time(results,cutoff=cutoff[e])

            robot_time.append(average_time)  # time per robot is sum of all average experiment times
            print(e, "average_time: ",average_time, time_var)
            agent_task_time.append(average_time)

            average_experiment_times.append(average_time)
            agent_task_time_var.append(time_var)

            mean_length, interval = p.get_average_n_trials(results, cutoff=cutoff[e])
            print(mean_length, interval)
            print("robot_number=",r)
            index = robots[robot_addr[r]].index(e)
            width = 0.1
            
            #x = r + (1+index-len(robots[robot_addr[r]])/2)*width
            x = count_agents/10 + count_bars*width #(1+index-len(robots[robot_addr[r]])/2)*width

            axes1.bar(x, mean_length, width, yerr=interval[1]-mean_length, color=colors[index])
            count_trials_overall.append(mean_length)
            axes1.set_ylim(0, 130)
            # axes1[count].set_xlim(1, len(mean_cost))
            # axes1[count].grid()
            # axes1[count].tick_params(axis="both", which="both", length=0)
            xticks.append(x)
            xticks_labels.append(e)
            axes1.set_xticks(xticks)
            axes1.set_xticklabels(xticks_labels, rotation=45, ha='right')
            
            #axes1[count].set_title(results[0].tags[1], y=1.0, pad=-14)
            axes1.set_xlabel("Tasks by Agents")
            axes1.set_ylabel("mean cost [1]")
            count_bars += 1
        count_agents += 1
        time_robots.append(robot_time) # time_robots collects all robot execution times
        agent_task_times.append(agent_task_time)  # for all agents the average times for their tasks [[cylinder_1,cylinder_2,..],[key_1,key_2,...],..]
        agent_task_times_var.append(agent_task_time_var)
    fig1.tight_layout()
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    print("trials overall = ",sum(count_trials_overall))
    print("time overall = ", max([sum(robot_time) for robot_time in time_robots])/60, "min")
    print("average experiment time = ", (sum(average_experiment_times)/n_tasks)/60, "min")
    plt.show(block=False)
    return max([sum(robot_time) for robot_time in time_robots])/60, agent_task_times, agent_task_times_var

def plot_single_robot_experiment(tags = "single_robot_learning_without"):
    #tags = ["single_robot_learning_without"]
    #tags = ["single_robot_learning_trans"]

    #default, collective_learning_04_alt
    robots = {  "collective-panda-prime": ["key_door"],
                "collective-panda-002": ["key_abus_e30"],
                "collective-panda-003": ["key_padlock","key_2"],
                "collective-panda-004": ["cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_50", "cylinder_60"], #
                "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
             }
    if tags == "single_robot_learning_without":
        robots = {  "collective-panda-prime": ["key_door"],
                    "collective-panda-002": ["key_abus_e30"],
                    "collective-panda-003": ["key_padlock","key_2"],
                    "collective-panda-004": ["cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_50", "cylinder_60"], #
                    "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
                }
    cutoff = {  "key_door":0.25,
                "key_abus_e30": 0.25,
                "key_padlock": 0.25,
                "key_2": 0.25,
                "cylinder_40": 0.45,
                "cylinder_10": 0.5,
                "cylinder_20": 0.35,
                "cylinder_30": 0.4,
                "cylinder_50": 0.35,
                "cylinder_60": 0.55,
                "HDMI_plug": 0.3,
                "key_padlock_2": 0.25,
                "key_hatch": 0.25,
                "key_old": 0.25
                }
    #for key in cutoff.keys():
    #    cutoff[key] = cutoff[key] * 1.5

    robot_addr = list(robots.keys())
    n_tasks = sum([len(tasks) for tasks in robots.values()])
    p = DataProcessor()
    experiments = ["collective_experiment"]
    colors = ["blue", "red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "coral", "brown", "lightgrey", "beige","lavender"]  # [:len(n_tasks)]
    legend_handles1 = []
    legend_handles2 = []

    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    count = 0
    robot_count = 0
    
    count_trials_overall = []
    count_time_overall = []
    xticks = []
    xticks_labels = []
    count_agents = 0
    count_bars = 0
    average_experiment_times = []
    experiment_time = []
    time_robots = []
    agent_task_times = []
    agent_task_times_var = []
    outsource = ("collective-panda-004",{"collective-panda-005": ["cylinder_10", "cylinder_30", "cylinder_50"]})
    for r in range(len(robot_addr)):
        task_count = 0
        title=False
        last_time = False
        robot_time = []
        agent_task_time = []
        agent_task_time_var = []
        for e in robots[robot_addr[r]]:
            filters = []
            filters.extend(tags)
            filters.append(e)
            print("tags = ", filters)
            results = get_multiple_experiment_data(robot_addr[r], "insertion", filter={"meta.tags": filters})
            if robot_addr[r] is "collective-panda-004":
                try:
                    outsource_data = get_multiple_experiment_data("collective-panda-005", "insertion", filter={"meta.tags": filters})
                    results.extend(outsource_data)
                    print("outsource data found",len(outsource_data))
                except DataNotFoundError:
                    pass
            indexes2pop = []
            tag_set = set()
            for i in range(len(results)):
                if len(results[i].costs) < 9:
                    indexes2pop.append(i)
                    continue
                if results[i] in tag_set:
                    indexes2pop.append(i)
                tag_set.add(str(results[i].tags))
            if indexes2pop:
                indexes2pop.reverse()
                for i in indexes2pop:
                    results.pop(i)

            average_time, time_var = p.get_average_time(results,cutoff=cutoff[e])

            robot_time.append(average_time)  # time per robot is sum of all average experiment times
            print(e, "average_time: ",average_time, time_var)
            agent_task_time.append(average_time)

            average_experiment_times.append(average_time)
            agent_task_time_var.append(time_var)

            mean_length, interval = p.get_average_n_trials(results, cutoff=cutoff[e])
            print(mean_length, interval)
            print("r=",r)
            width = 0.1
            
            #x = r + (1+index-len(robots[robot_addr[r]])/2)*width
            x = count_agents/10 + count_bars*width #(1+index-len(robots[robot_addr[r]])/2)*width
            print("task number: ",count_bars)
            axes1.bar(x, mean_length, width, yerr=interval[1]-mean_length, color=colors[count_bars])
            count_trials_overall.append(mean_length)
            axes1.set_ylim(0, 130)
            # axes1[count].set_xlim(1, len(mean_cost))
            # axes1[count].grid()
            # axes1[count].tick_params(axis="both", which="both", length=0)
            xticks.append(x)
            xticks_labels.append(e)
            axes1.set_xticks(xticks)
            axes1.set_xticklabels(xticks_labels, rotation=45, ha='right')
            
            #axes1[count].set_title(results[0].tags[1], y=1.0, pad=-14)
            axes1.set_xlabel("Tasks by Agents")
            axes1.set_ylabel("mean cost [1]")
            count_bars += 1
        count_agents += 1
        time_robots.append(robot_time) # time_robots collects all robot execution times
        agent_task_times.append(agent_task_time)  # for all agents the average times for their tasks [[cylinder_1,cylinder_2,..],[key_1,key_2,...],..]
        agent_task_times_var.append(agent_task_time_var)
    fig1.tight_layout()
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    print("trials overall = ",sum(count_trials_overall))
    print("time overall = ", sum([sum(robot_time) for robot_time in time_robots])/60, "min")
    print("average experiment time = ", (sum(average_experiment_times)/n_tasks)/60, "min")
    plt.show(block=False)
    return sum([sum(robot_time) for robot_time in time_robots])/60, agent_task_times, agent_task_times_var

def plot_collective_overview():
    cm = 1/2.54
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2, figsize=(20*cm,20*cm))
    axes1.set_xlabel("#agents [1]")
    axes1.set_ylabel("time [min]")
    single_trans,_,_ = plot_single_robot_experiment(["single_robot_learning_trans"])
    collective_5,_,_ = plot_collective_experiment(["collective_learning_04_alt"])
    collective_6,_,_ = plot_collective_experiment(["collective_learning_04_ext_alt"])
    print("\n plot this: ",[1,5,6],[single_trans,collective_5,collective_6])
    axes1.plot([1,5,6],[single_trans,collective_5,collective_6], label="14 tasks")
    axes1.scatter([1,5,6],[single_trans,collective_5,collective_6], s=120, marker="X", color="orange")#, markersize=12)
    single_without,_,_ = plot_single_robot_experiment(["single_robot_learning_without"])
    parallel,_,_ = plot_collective_experiment(["collective_learning_parallel"])
    axes1.scatter([1,5],[single_without, parallel], s=120, marker="X", label = "14 tasks", color="orange")
    axes1.text(1.1,single_without-4,"without memory", fontsize=14) 
    axes1.text(1.1,single_trans+4,"transfer", fontsize=14)
    axes1.text(4.2,parallel+3,"local transfer", fontsize=14)
    axes1.text(4.2,collective_5-2.4,"collective", fontsize=14)
    axes1.text(5.4,collective_6+2,"collective", fontsize=14)
    #axes1.annotate("single trans", xy=(1,single_trans), xytext=(1.2,single_trans+10),arrowprops=dict(facecolor="k", shrink=0.15, width=1,headwidth=5),) 
    #axes1.annotate("parallel", xy=(5,parallel), xytext=(4.5,parallel+10),arrowprops=dict(facecolor="k", shrink=0.15, width=1,headwidth=5),) 
    #axes1.annotate("collective", xy=(5,collective_5), xytext=(4.2,collective_5-5),arrowprops=dict(facecolor="k", shrink=0.15, width=0,headwidth=0),) 
    #axes1.annotate("collective", xy=(6,collective_6), xytext=(5.5,collective_6+10),arrowprops=dict(facecolor="k", shrink=0.15, width=1,headwidth=5),) 

    axes1.set_title("learning 14 task")
    fig1.tight_layout()
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    plt.show(block=False)

def collective_plot():
    def acending_sublist(list_of_lists):
        '''add total times of tasks to get time-points:'''
        sublists_ascending = []
        for agent_tasks in list_of_lists:
            agent_added = []
            for i in range(len(agent_tasks)):
                #add total times of tasks to get time-points:
                agent_added.append(sum(agent_tasks[:i+1]))
            sublists_ascending.append(agent_added)
        return sublists_ascending
    def ascending_list(l):
        ascending_l = []
        for i in range(len(l)):
            ascending_l.append(sum(l[:i+1]))
        return ascending_l
    def acending_sublist_touple(list_of_lists):
        '''add total times of tasks to get time-points:'''
        sublists_ascending = []
        for agent_tasks in list_of_lists:
            agent_added = []
            for i in range(len(agent_tasks)):
                #add total times of tasks to get time-points:
                if i == 0:
                    agent_added.append(agent_tasks[i])
                else:
                    t = (agent_added[i-1][0]+agent_tasks[i][0],agent_added[i-1][1]+agent_tasks[i][1])
                    agent_added.append(t)
            sublists_ascending.append(agent_added)
        return sublists_ascending
    def ascending_list_touple(l):
        ascending_l = []
        for i in range(len(l)):
            if i == 0:
                ascending_l.append(l[i])
            else:
                t = (ascending_l[i-1][0]+l[i][0],ascending_l[i-1][1]+l[i][1])
                ascending_l.append(t)
        return ascending_l

    _,single_trans, single_trans_var = plot_single_robot_experiment(["single_robot_learning_trans"])
    _,single_without, single_without_var = plot_single_robot_experiment(["single_robot_learning_without"])
    _,collective_5, collective_5_var = plot_collective_experiment(["collective_learning_04_alt"])
    _,collective_6, collective_6_var = plot_collective_experiment(["collective_learning_04_ext_alt"])
    _,parallel, parallel_var = plot_collective_experiment(["collective_learning_parallel"])
    #mean
    #flatten first -> pretend all tasks are done by one robot
    single_trans_flatten = [average_task_time for agent in single_trans for average_task_time in agent] #flatten
    single_without_flatten = [average_task_time for agent in single_without for average_task_time in agent] #flatten
    single_trans_added = ascending_list(single_trans_flatten)
    single_without_added = ascending_list(single_without_flatten)
    collective_5_added = acending_sublist(collective_5)
    collective_6_added = acending_sublist(collective_6)
    parallel_added = acending_sublist(parallel)
    collective_5_added = [average_task_time for agent in collective_5_added for average_task_time in agent] #flatten
    collective_6_added = [average_task_time for agent in collective_6_added for average_task_time in agent] #flatten
    parallel_added = [average_task_time for agent in parallel_added for average_task_time in agent] #flatten
    #var
    #flatten first -> pretend all tasks are done by one robot
    single_trans_flatten_var = [average_task_time for agent in single_trans_var for average_task_time in agent] #flatten
    single_without_flatten_var = [average_task_time for agent in single_without_var for average_task_time in agent] #flatten
    single_trans_added_var = ascending_list_touple(single_trans_flatten_var)
    single_without_added_var = ascending_list_touple(single_without_flatten_var)
    collective_5_added_var = acending_sublist_touple(collective_5_var)
    collective_6_added_var = acending_sublist_touple(collective_6_var)
    parallel_added_var = acending_sublist_touple(parallel_var)
    collective_5_added_var = [average_task_time for agent in collective_5_added_var for average_task_time in agent] #flatten
    collective_6_added_var = [average_task_time for agent in collective_6_added_var for average_task_time in agent] #flatten
    parallel_added_var = [average_task_time for agent in parallel_added_var for average_task_time in agent] #flatten

    #sort
    zipped_lists = zip(collective_5_added, collective_5_added_var)
    sorted_pairs = sorted(zipped_lists, key=lambda pair: pair[0])
    tuples = zip(*sorted_pairs)
    collective_5_added, collective_5_added_var = [ list(tuple) for tuple in  tuples]

    zipped_lists = zip(collective_6_added, collective_6_added_var)
    sorted_pairs = sorted(zipped_lists, key=lambda pair: pair[0])
    tuples = zip(*sorted_pairs)
    collective_6_added, collective_6_added_var = [ list(tuple) for tuple in  tuples]

    zipped_lists = zip(parallel_added, parallel_added_var)
    sorted_pairs = sorted(zipped_lists, key=lambda pair: pair[0])
    tuples = zip(*sorted_pairs)
    parallel_added, parallel_added_var = [ list(tuple) for tuple in  tuples]

    # add time zero to beginning:
    collective_5_added.insert(0,0)
    collective_5_added_var.insert(0,(0,0))
    collective_6_added.insert(0,0)
    collective_6_added_var.insert(0,(0,0))
    parallel_added.insert(0,0)
    parallel_added_var.insert(0,(0,0))
    single_trans_added.insert(0,0)
    single_trans_added_var.insert(0,(0,0))
    single_without_added.insert(0,0)
    single_without_added_var.insert(0,(0,0))


    cm = 1/2.54
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=3, figsize=(20*cm,20*cm))
    axes1.set_xlabel("time [min]")
    axes1.set_ylabel("#solved tasks")

    coll_5_handle, = axes1.plot([x/60 for x in collective_5_added],list(range(len(collective_5_added))), label="5 agent collective", color='b')
    #collective_5_added_interval_low = [collective_5_added_var[i][0]/60 for i in range(len(collective_5_added))]
    #collective_5_added_interval_high = [collective_5_added_var[i][1]/60 for i in range(len(collective_5_added))]
    #axes1.fill_betweenx(list(range(len(collective_5_added))), collective_5_added_interval_low, collective_5_added_interval_high, color='b', alpha=.1)

    coll_6_handle, = axes1.plot([x/60 for x in collective_6_added],list(range(len(collective_6_added))), label="6 agent collective", color='orange')
    #collective_6_added_interval_low = [collective_6_added_var[i][0]/60 for i in range(len(collective_6_added))]
   # collective_6_added_interval_high = [collective_6_added_var[i][1]/60 for i in range(len(collective_6_added))]
   # axes1.fill_betweenx(list(range(len(collective_6_added))), collective_6_added_interval_low, collective_6_added_interval_high, color='orange', alpha=.1)

    parallel_handle, = axes1.plot([x/60 for x in parallel_added],list(range(len(parallel_added))), label="5 agent local transfer (parallel)", color="green")
    #parallel_added_interval_low = [parallel_added_var[i][0]/60 for i in range(len(parallel_added))]
    #parallel_added_interval_high = [parallel_added_var[i][1]/60 for i in range(len(parallel_added))]
    #axes1.fill_betweenx(list(range(len(parallel_added))), parallel_added_interval_low, parallel_added_interval_high, color='green', alpha=.1)

    without_handle, = axes1.plot([x/60 for x in single_without_added],list(range(len(single_without_added))), label="1 agent without memory",color = "red")
    #single_without_interval_low = [single_without_added_var[i][0]/60 for i in range(len(single_without_added_var))]
    #single_without_interval_high = [single_without_added_var[i][1]/60 for i in range(len(single_without_added_var))]
    #axes1.fill_betweenx(list(range(len(single_without_added))), single_without_interval_low, single_without_interval_high, color='red', alpha=.1)

    trans_handle, = axes1.plot([x/60 for x in single_trans_added],list(range(len(single_trans_added))), label="1 agent transfer",color="purple")
    #single_trans_added_interval_low = [single_trans_added_var[i][0]/60 for i in range(len(single_trans_added))]
    #single_trans_added_interval_high = [single_trans_added_var[i][1]/60 for i in range(len(single_trans_added))]
    #axes1.fill_betweenx(list(range(len(single_trans_added))), single_trans_added_interval_low, single_trans_added_interval_high, color='purple', alpha=.1)
    
    plt.legend(handles=[coll_5_handle,coll_6_handle,parallel_handle,without_handle,trans_handle])

    axes1.set_xlim((0,max(single_without_added)/60+5))
    axes1.set_title("learning 14 task")
    fig1.tight_layout()
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    plt.show(block=False)

def success_cost():
    robots = {  "collective-panda-prime": ["key_door"],
                "collective-panda-002": ["key_abus_e30"],
                "collective-panda-003": ["key_padlock", "key_2"], #
                "collective-panda-004": ["cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_50", "cylinder_60"], #  
                "collective-panda-008": [ "HDMI_plug", "key_padlock_2", "key_hatch", "key_old"] # 
             }
    p = DataProcessor()
    tags = ["collective_learning"]
    fig2, axes2 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2)
    for robot in robots.keys():
        for insertable in robots[robot]:
            filter = copy.deepcopy(tags)
            filter.append(insertable)
            results = get_multiple_experiment_data(robot, "insertion", filter={"meta.tags": filter})
            indexes2pop = []
            for i in range(len(results)):
                if len(results[i].trials) < 130:
                    #print(results[i].tags)
                    indexes2pop.append(i)
            indexes2pop.reverse()
            for i in indexes2pop:
                results.pop(i)
            successes = [item for sublist in p.get_cost_of_successes(results) for item in sublist]
            successes.sort()
            best_cost = successes[0]
            worst_cost = successes[-1]
            mean_cost = np.mean(successes)
            print(filter)
            print("best_cost: ",best_cost,"\nmean_cost: ",mean_cost,"\nworst_cost", worst_cost)


def plot_collective_demo():
    def isNaN(num):
        return num != num
    tags = ["dualarm_demo"]
    p = DataProcessor()
    experiments = {
                   # "10.157.175.221":   "001_left", #0 ms            collective-001.local  
                    "10.157.174.166":   "002_left",#0 ms            collective-002.local  
                    "10.157.174.167":   "003_left", #0 ms            collective-003.local   
                    "10.157.174.168":   "004_left", #0 ms            collective-004.local   
                    "10.157.174.89" :   "005_left", #0 ms            collective-005.local   
                    "10.157.174.80" :   "006_left",#0 ms            collective-006.local   
                    "10.157.174.200":   "007_left",#0 ms            collective-007.local   
                    "10.157.175.129":   "008_left", #0 ms            collective-008.local   
                    "10.157.174.36" :   "009_left",#0 ms            collective-009.local 
                    "10.157.174.59":    "010_left",                #collective-010#  
                   # "10.157.175.87":    "011_left",#0 ms            collective-011.local
                    "10.157.174.241":   "012_left",#0 ms            collective-012.local
                    "10.157.174.201":   "013_left",#0 ms            collective-013.local
                    "10.157.174.247":   "014_left",#0 ms            collective-014.local   
                    "10.157.174.202":   "015_left",#0 ms            collective-015.local
                    "10.157.174.203":   "016_left",#0 ms            collective-016.local    
                    "10.157.174.46":    "017_left",#0 ms            collective-017.local    
                    "10.157.174.103":   "018_left",#0 ms            collective-018.local    
                    "10.157.174.206":   "019_left",#0 ms            collective-019.local   
                    "10.157.174.204":   "020_left",#0 ms            collective-020.local    
                    "10.157.175.173":   "021_left",#0 ms            collective-021.local    
                    "10.157.174.244":   "022_left",#0 ms            collective-022.local   
                    "10.157.174.205":   "023_left",#0 ms            collective-023.local    
                    "10.157.175.156":   "024_left",#0 ms            collective-024.local    
                    "10.157.174.186":   "025_left",#0 ms            collective-025.local    
                    "10.157.174.245":   "026_left", #0 ms            collective-026.local    
                    "10.157.174.249":   "027_left",#0 ms            collective-027.local   
                    "10.157.174.255":   "028_left",#0 ms            collective-028.local    
                    #"10.157.174.42":    "029_left",#0 ms            collective-029.local    
                    "10.157.174.163":   "038_left",
                    "10.157.174.175":   "039_left",
                    "10.157.174.52" :   "046_left",
                    "10.157.175.134":   "050_left",
                }
    learning_times_mean = []
    learning_times_interval = []
    for r in experiments.keys():
        insertable = experiments[r]
        results = get_multiple_experiment_data(r, "insertion", filter={"meta.tags": tags})
        indexes2pop = []
        average_time = 0
        for i in range(len(results)):
            if len(results[i].costs) < 9:
                indexes2pop.append(i)
                continue
            average_time += results[i].total_time
        if indexes2pop:
            indexes2pop.reverse()
        for i in indexes2pop:
            results.pop(i)
        indexes2pop = []
        for i in range(len(results)):  # consider 8 succeses as learned
            successes = results[i].get_successes_per_trial()
            success_indexes = [index for index,success in enumerate(successes) if success is True]

            if len(success_indexes)>=8:
                results[i].trials = results[i].trials[:success_indexes[7]+1]  # cut off results at 8th success
            else:
                indexes2pop.append(i)
        if indexes2pop:
            indexes2pop.reverse()
            for i in indexes2pop:
                results.pop(i)

        # mean learning time
        learning_times = []
        for result in results:
            learning_time = 0
            for t in result.trials:
                if t["t_delta"] < 10:
                    learning_time+=t["t_delta"]
            if type(learning_time) is float:
                learning_times.append(learning_time)
        if len(learning_times) > 15:
            print(learning_times[15])
        learning_time_mean = np.mean(learning_times)
        learning_time_interval = scipy.stats.t.interval(alpha=0.95, df=len(learning_times)-1, loc=np.mean(learning_times), scale=scipy.stats.sem(learning_times))
        learning_times_mean.append(learning_time_mean)
        learning_times_interval.append(learning_time_interval)
    #sort for collective plot:
    print(learning_times_mean)
    indexes2pop=[]
    for i,(mean, interval) in enumerate(zip(learning_times_mean, learning_times_interval)):
        if isNaN(mean):
            indexes2pop.append(i)
    if indexes2pop:
        indexes2pop.reverse()
        for i in indexes2pop:
            learning_times_mean.pop(i)
            learning_times_interval.pop(i)

    sorted_learning_data = sorted(zip(learning_times_interval, learning_times_mean), key=lambda x: x[1])
    learning_times_mean = [x[1] for x in sorted_learning_data]
    learning_times_interval = [x[0] for x in sorted_learning_data]
    print(learning_times_mean)
    #plot
    learning_times_interval.insert(0, (0,0))
    learning_times_mean.insert(0,0)
    fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    axes1.set_xlabel("Time [s]")
    axes1.set_ylabel("learned Skills [1]")
    print(len(learning_times_mean))
    axes1.plot(learning_times_mean, list(range(len(learning_times_mean))))
    lower_interval = [x[0] for x in learning_times_interval]
    upper_interval = [x[1] for x in learning_times_interval]
    axes1.fill_betweenx(list(range(len(learning_times_mean))), lower_interval, upper_interval, alpha=0.2)
    axes1.set_xlim(0,600)
    axes1.set_ylim(0,32)
    plt.show()


def plot_simple_learning():
    robots = ["collective-panda-004"]
    p = DataProcessor()

    tags = ["simple_learning2"]
    experiments = ["with_Kfold", "without_Kfold"]
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"][:len(experiments)]
    legend_handles1 = []
    legend_handles2 = []
    fig1, axes1 = plt.subplots(len(robots), 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    fig2, axes2 = plt.subplots(len(robots), 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2)
    if len(robots) == 1:
        axes1 = [axes1]
        axes2 = [axes2]
    for r in range(len(robots)):
        for e in range(len(experiments)):
            filters = []
            filters.extend(tags)
            filters.append(experiments[e])
            print("tags = ", filters)
            results = get_multiple_experiment_data(robots[r], "insertion", filter={"meta.tags": {"$all": filters}})
            indexes2pop = []
            for i in range(len(results)):
                if len(results[i].trials) < 130:
                    #print("no complete set. ",len(results[i].trials))
                    #print(results[i].tags)
                    indexes2pop.append(i)
            indexes2pop.reverse()
            for i in indexes2pop:
                results.pop(i)
            print("number of experiments (",experiments[e], ") = ", len(results))
            #mean_cost, confidence = p.get_average_cost(results, True, 10)

            # monocally decreasing cost:
            mean_cost, confidence = p.get_average_cost_over_trials(results, True, 1, specification="all")
            axes1[r].fill_between(np.linspace(1, len(mean_cost), len(mean_cost)), mean_cost - confidence, mean_cost + confidence * 5, alpha=0.2, color=colors[e])
            legend_handle1, = axes1[r].plot([i+1 for i in range(len(mean_cost))], mean_cost, linewidth=2, color=colors[e], label=experiments[e])
            legend_handles1.append(legend_handle1)

            axes1[r].set_ylim(0, 2.4)
            axes1[r].set_xlim(1, len(mean_cost))
            axes1[r].grid("on")
            axes1[r].tick_params(axis="both", which="both", length=0)
            xticks = [i*10 for i in range(1,(int(len(mean_cost)/10)) +1)]
            xticks.insert(0,1)
            axes1[r].set_xticks(xticks)
            axes1[r].set_title(results[0].tags[1], y=1.0, pad=-14)
            axes1[r].set_xlabel("Trial [1]")
            if r == 0:
                axes1[r].set_ylabel("Cost [1]")
                axes1[r].legend(legend_handles1, experiments, loc='upper right')#, experiments)
            
            # batchwise plot:
            mean_cost, confidence = p.get_average_cost_over_trials(results, False, 10, specification="all")
            axes2[r].fill_between(np.linspace(1, len(mean_cost), len(mean_cost)), mean_cost - confidence, mean_cost + confidence * 5, alpha=0.2, color=colors[e])
            legend_handle2, = axes2[r].plot([i+1 for i in range(len(mean_cost))], mean_cost, linewidth=2, color=colors[e], label=experiments[e])
            legend_handles2.append(legend_handle2)

            axes2[r].set_ylim(0, 2.4)
            axes2[r].set_xlim(1, len(mean_cost))
            axes2[r].grid()
            axes2[r].tick_params(axis="both", which="both", length=0)
            axes2[r].set_title(results[0].tags[1], y=1.0, pad=-14)
            axes2[r].set_xlabel("Trial [1]")
            if r == 0:
                axes2[r].set_ylabel("Cost [1]")
                axes2[r].legend(legend_handles2, experiments, loc='upper right')#, experiments)

    plt.show()


def plot_pitstop_bravo():
    new_cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088}
    colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]  # [:len(n_tasks)]
    # fig1, axes1 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=1)
    
    print("\ngetting data - collective with 5 agents")
    mean = []
    upper_boundary = []
    lower_boundary = []
    tags = [["ps_bravo_5","ReqR"+str(sr)] for sr in [0, 0.2, 0.6, 0.8, 1]]
    print("-------------------------------------------------")
    tags.insert(2, ["5agents_25tasks","collective"])
    print(tags)
    print("-------------------------------------------------")
    
    for tag in tags:
        try:
            if tag == ["5agents_25tasks","collective"]:
                temp_a, temp_b = get_big_collective_data(tag)
            else:
                temp_a, temp_b = get_big_collective_data(tag ,cutoff=new_cutoff)
                               
            mean.append(temp_a[-1]/60)
            lower_boundary.append(temp_b[-1][0]/60)
            upper_boundary.append(temp_b[-1][1]/60)
        except:
            print("888888888888888888")
            print(tag)
    
    range = [0, 0.2, 0.4, 0.6, 0.8, 1]
    plt.plot(range, mean)
    plt.fill_between(range, lower_boundary, upper_boundary, alpha=0.2)
    plt.xlabel("request rate")
    plt.ylabel("learning time [min]")
    plt.title("5 agents 25 tasks with distinct request rate")
    plt.grid(True)
    plt.savefig("Pitstop Bravo.png")
    
    # save to csv
    

   

    # print("total learning time comparison")
    # fig2, axes2 = plt.subplots(1, 1, sharex=True, gridspec_kw={'hspace': 0, 'wspace': 0.2}, num=2)
    # y = []
    # var = []
    # for time,confidence in zip([mean_collective_5,mean_collective_6,mean_collective_7,mean_collective_8,mean_collective_9,mean_collective_10], [
    #     (lower_bound_confindece_collective_5[-1], upper_bound_confindece_collective_5[-1]),
    #     (lower_bound_confindece_collective_6[-1], upper_bound_confindece_collective_6[-1]),
    #     (lower_bound_confindece_collective_7[-1], upper_bound_confindece_collective_7[-1]),
    #     (lower_bound_confindece_collective_8[-1], upper_bound_confindece_collective_8[-1]),
    #     (lower_bound_confindece_collective_9[-1], upper_bound_confindece_collective_9[-1]),
    #     (lower_bound_confindece_collective_10[-1], upper_bound_confindece_collective_10[-1]),
        
    # ]):
    #     y.append(time[-1])
    #     var.append(confidence)
    # print(var)
    # axes2.plot(range(5,11),y,label="agent dependent total learning time (25 tasks)")
    # axes2.fill_between(range(5,11), [v[0] for v in var], [v[1] for v in var], alpha=0.2)
    # axes2.set_ylim(0,200)
    # axes2.set_ylabel("learning time [min]")
    # axes2.set_xlabel("number of agents")
    # axes2.set_title("collective with 25 tasks")
    # axes2.grid()
    # axes2.legend(loc="upper right", fontsize=14)
    # plt.show(block=False)


def cost_process(c:list):
    s = 100
    r = []
    for i in c:
        s = min(i, s)
        r.append(s)
    
    return r

def cost_list2curve(cost_list):
    length = max([len(l) for l in cost_list])
    # print(length)
    r = []
    for l in cost_list:
        r.append(l + (length - len(l)) * [l[-1]])
        # print(len(l))
    
    m = np.array(r)
    mean = np.mean(m,0)
    std = np.std(m,0)
    
    
    # plt.plot(list(range(1, length+1)), mean)
    # plt.plot(list(range(1, length+1)), mean-std)
    # plt.plot(list(range(1, length+1)), mean+std)
    # plt.savefig("xxx.png")
    return [mean, std]
        
cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
            '003_left': 0.68016,
            '004_left': 0.74976,
            '005_left': 0.65, #
            '006_left': 0.6127199999999999,
            '007_left': 0.62616,
            '008_left': 0.6371999999999999,
            '010_left': 0.6888000000000001,
            '011_left': 0.63816,
            '012_left': 0.75528,
            '009_left': 0.6943199999999999,
            '013_left': 0.6348,
            '014_left': 0.6,
            '015_left': 0.68184,
            '016_left': 0.9,   #
            '017_left': 0.63864,
            '041_left': 0.63144,  # '018_left': 0.63144,
            '021_left': 0.63528,
            '022_left': 0.6828000000000001,
            '023_left': 0.6648000000000001,
            '024_left': 0.9187199999999999,
            '025_left': 0.64752,
            '027_left': 0.68448,
            '028_left': 0.61824,
            '029_left': 0.68088}

new_cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                    '003_left': 0.68016,
                    '004_left': 0.74976,
                    '005_left': 0.65, #
                    '006_left': 0.6127199999999999,
                    '007_left': 0.62616,
                    '008_left': 0.6371999999999999,
                    '010_left': 0.6888000000000001,
                    '011_left': 0.63816,
                    '012_left': 0.75528,
                    '009_left': 0.6943199999999999,
                    '013_left': 0.6348,
                    '014_left': 0.6,
                    '015_left': 0.68184,
                    '016_left': 0.9,   #
                    '017_left': 0.63864,
                    '041_left': 0.63144,  # '018_left': 0.63144,
                    '021_left': 0.63528,
                    '022_left': 0.6828000000000001,
                    '023_left': 0.6648000000000001,
                    '024_left': 0.9187199999999999,
                    '025_left': 0.64752,
                    '027_left': 0.68448,
                    '028_left': 0.61824,
                    '029_left': 0.68088}
  
    
def fetch_data(cutoff= new_cutoff, mode = 0):
    # 1: for psp, with 
    robots = list_block_1 + list_block_2 + list_U
    print(robots)
    # tags = ["5agents_25tasks_local","isolated_local_noFastPipeline"]
    tags = "CMAES"
    dir = "data17/cmaes_data/"
    if mode == 1:
        tags = ["5agents_25tasks_local","isolated_local_noFastPipeline"]
        dir = "data17/psp_data/"
    ret = []
    
    
    # for xxx in robots:
    for xxx in robots:
        # if xxx == "041" and mode == 1:
        #     continue
        
        
        results = get_multiple_experiment_data("collective-"+xxx+".rsi.ei.tum.de", "insertion", "ml_results", {"meta.tags": tags})
        cost_list = []
        for result in results:
            # print("length", len(result.costs))                
            if len(result.costs) < 10:
                continue
        
            if min(result.costs) <= cutoff[xxx+"_left"]:
                cost_list.append(cost_process(result.costs))
        
        
        if len(cost_list)>0:
            ret.append( cost_list2curve(cost_list) ) 
            # print("-------------", xxx)

            with open(dir + xxx + '.pickle', 'wb') as file:
                pickle.dump(cost_list2curve(cost_list), file) 
        
        else:
            print(xxx + "cutoff issue")
            try:
                print("min_cost", min([ min(i.costs) for i in results]))
            except:
                print("costs missing in results")
                
            print("cut_off", cutoff[xxx+"_left"])

    return ret
