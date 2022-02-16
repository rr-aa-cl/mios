from math import isclose
import numpy as np
from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor
from plotting.data_processor import DataError
from plotting.plotter import Plotter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d import Axes3D
import csv
import scipy.stats

plot = Plotter()


def plot_single_experiment(host: str, task_type: str, database: str, tags: list = None, uuid: str = None):
    p = DataProcessor()

    if tags is not None:
        result = get_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags}})
    elif uuid is not None:
        result = get_experiment_data(host, task_type, results_db=database, uuid=uuid)
    else:
        return
    cost, confidence = result.get_cost_per_time()
    cost_mono = p.get_monotonically_decreasing_cost(cost)
    plt.plot(cost_mono)
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
                    print("Processing plot " + str(i * 10 + j + 1), end="\r")
                    tags = ["transfer_learning", tasks[i]]
                    results = get_multiple_experiment_data("collective-control-001.local", "insert_object",
                                                           results_db="results_tl_base",
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
    p = DataProcessor()
    plot = Plotter()
    tags = ["transfer_learning", task]
    results = get_multiple_experiment_data("collective-control-001.local", "insert_object",
                                           results_db="transfer_base_v2",
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
    plt.xlim([0, 10])
    plt.ylim([0, 1])
    plt.show()


def plot_transfer_learning_3():
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60",
             "key_pad", "key_old", "key_hatch"]
    task_colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]

    n_cols = 3
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
            axes[i, j].set_title(tasks[i * n_rows + j], y=1.0, pad=-14)
            legend = []
            try:
                tags = ["transfer_learning", tasks[i * n_rows + j]]
                results = get_multiple_experiment_data("localhost", "insert_object",
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
                legend = [tasks[i * n_rows + j]]
                legend_casr = ["Optimal CASR", tasks[i * n_rows + j]]
            except (DataNotFoundError, DataError):
                print("Base cost for task " + tasks[i] + " not found.")
                continue
            for t in range(len(tasks)):
                try:
                    tags = ["transfer_learning", tasks[i * n_rows + j], "from_" + tasks[t]]
                    results = get_multiple_experiment_data("localhost", "insert_object",
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
                    le_ratio_matrix[i * n_rows + j][t] = le_transfer / le_base
                    kl_matrix[i * n_rows + j][t] = calculate_kl_divence(base_cost, cost)
                    casr_matrix[i * n_rows + j][t] = np.sum(casr) / np.sum(base_casr)

                    speedup_matrix[i * n_rows + j][t] = calculate_speedup(base_cost, cost)
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
                axes[i, j].set_yticks([2, 4, 6, 8, 10])
                axes[i, j].set_yticklabels(["2", "4", "6", "8", "10"])
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
            ax.xlabel("Episode [1]")
            ax_casr.xlabel("Episode [1]")
        else:
            ax.xlabel("Trial [1]")
            ax_casr.xlabel("Episode [1]")
    else:
        ax.set_xlabel("Time [s]", fontsize=12)
        ax_casr.set_xlabel("Time [s]")
    ax.set_ylabel("Execution time [s]", fontsize=12)
    ax_casr.set_ylabel("CASR [1]", fontsize=12)

    fig.set_size_inches(16, 9)
    fig_casr.set_size_inches(16, 9)
    fig.savefig("results_cost.png", bbox_inches='tight', dpi=300)
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
        'text.latex.preamble': [r'\usepackage{amssymb}',r'\usepackage{amsmath}',r'\usepackage{mathbbol}'],
        "font.family": 'serif',
        "font.size": 16
    })
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60",
             "key_pad", "key_old", "key_hatch"]
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

    n_cols = 3
    n_rows = 3

    episode_wise = False
    trial_wise = False
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
            axes[i, j].set_title("Task: " + task_title[tasks[i * n_rows + j]], x=0.1, y=0.13, pad=-14, fontsize=16)
            axes_casr[i, j].set_title("Task: " + task_title[tasks[i * n_rows + j]], y=1.0, pad=-14, fontsize=16)
            try:
                tags = ["transfer_learning", tasks[i * n_rows + j]]
                results = get_multiple_experiment_data("localhost", "insert_object",
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
                base_casr = np.insert(base_casr, 0, 0)
                base_dcasr = np.diff(base_casr)
                dcasr_set[i * n_rows + j].append(base_dcasr)
                base_cost_log = np.log10(base_cost + 1)
                time_log = []
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
                print("Base cost for task " + tasks[i] + " not found.")
                continue

            cost_cylinders = []
            casr_cylinders = []
            cost_keys = []
            casr_keys = []
            for t in range(len(tasks)):
                try:
                    tags = ["transfer_learning", tasks[i * n_rows + j], "from_" + tasks[t]]
                    results = get_multiple_experiment_data("localhost", "insert_object",
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

                    if tasks[t] == tasks[i * n_rows + j]:
                        axes[i, j].plot(time_log, cost_log, zorder=1, color=color_level_0, linestyle="dashed", label="Level-0-Transfer", linewidth=2)
                        asr_mean, asr_std = get_mean_over_window(np.diff(casr))
                        axes_casr[i, j].stairs(asr_mean, zorder=1, color=color_level_0, linestyle="dashed", label="Level-0-Transfer", linewidth=2)
                        #legend.append("Level-0-Transfer")#: " + tasks[t])
                        dcasr_set[i * n_rows + j].append(np.diff(casr))
                    else:
                        if tasks[t].split("_")[0] == "cylinder":
                            cost_cylinders.append(cost_log)
                            casr_cylinders.append(casr)
                        if tasks[t].split("_")[0] == "key":
                            cost_keys.append(cost_log)
                            casr_keys.append(casr)

                except (DataNotFoundError, DataError):
                    pass

            mean_cost_cylinders = [0] * 1500
            mean_casr_cylinders = [0] * 1500
            mean_cost_keys = [0] * 1500
            mean_casr_keys = [0] * 1500
            std_cost_cylinders = [0] * 1500
            std_casr_cylinders = [0] * 1500
            std_cost_keys = [0] * 1500
            std_casr_keys = [0] * 1500
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

                std_cost_cylinders[k] = np.sqrt(std_cost / len(cost_keys))
                std_casr_cylinders = np.sqrt(std_casr / len(casr_keys))

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

            time_log = []
            for k in range(1500):
                time_log.append(np.log10(k))

            cylinder_asr_mean, cylinder_asr_std = get_mean_over_window(np.diff(mean_casr_cylinders))
            keys_asr_mean, keys_asr_std = get_mean_over_window(np.diff(mean_casr_keys))
            if tasks[i * n_rows + j].split("_")[0] == "cylinder":
                dcasr_set[i * n_rows + j].append(mean_dcasr_cylinders)
                dcasr_set[i * n_rows + j].append(mean_dcasr_keys)
                axes[i, j].plot(time_log, mean_cost_cylinders, zorder=1, color=color_level_1, linestyle="dotted", label="Level-1-Transfer", linewidth=2)
                axes[i, j].plot(time_log, mean_cost_keys, zorder=1, color=color_level_2, linestyle="dashdot",  label="Level-2-Transfer", linewidth=2)
                axes_casr[i, j].stairs(cylinder_asr_mean, linestyle="dotted", zorder=1, color=color_level_1, label="Level-1-Transfer", linewidth=2)
                axes_casr[i, j].stairs(keys_asr_std, linestyle="dashdot", zorder=1, color=color_level_2, label="Level-2-Transfer", linewidth=2)
            else:
                dcasr_set[i * n_rows + j].append(mean_dcasr_keys)
                dcasr_set[i * n_rows + j].append(mean_dcasr_cylinders)
                axes[i, j].plot(time_log, mean_cost_cylinders, zorder=1, color=color_level_2, linestyle="dotted",
                                label="Level-2-Transfer")
                axes[i, j].plot(time_log, mean_cost_keys, zorder=1, color=color_level_1, linestyle="dashdot",
                                label="Level-1-Transfer")
                axes_casr[i, j].stairs(keys_asr_mean, linestyle="dashdot", zorder=1, color=color_level_1, label="Level-1-Transfer", linewidth=2)
                axes_casr[i, j].stairs(cylinder_asr_mean, linestyle="dotted", zorder=1, color=color_level_2, label="Level-2-Transfer", linewidth=2)

            if i == 0 and j == 0:
                current_handles, current_labels = axes[i, j].get_legend_handles_labels()
                new_lables = [current_labels[1], current_labels[2], current_labels[3], current_labels[0]]
                new_handles = [current_handles[1], current_handles[2], current_handles[3], current_handles[0]]
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
            ax.xlabel("Trial [1]")
            ax_casr.xlabel("Trial [1]")
    else:
        ax.set_xlabel(r"Learning Time [$\text{log}_{10}$(s)]", fontsize=16)
        ax_casr.set_xlabel(r"Learning Time [s]", fontsize=16)
    ax.set_ylabel(r"Execution Time [$\text{log}_{10}$(s)]", fontsize=16)
    ax_casr.set_ylabel(r"ALSR [1]", fontsize=16)
    ax_casr.yaxis.set_label_coords(-0.05, 0.5)

    fig.set_size_inches(16, 9)
    fig_casr.set_size_inches(16, 9)
    fig.savefig("results_cost.png", bbox_inches='tight', dpi=300)
    fig_casr.savefig("results_calsc.png", bbox_inches='tight', dpi=300)

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


def live_plotting():
    from plotting.live_plotter import live_plot
    # lp = LivePlotter([],[])
    # lp.start_plot()
    robots = ["collective-panda-001.local", "collective-panda-002.local",
              "collective-panda-003.local", "collective-panda-009.local"]
    tags = ["live_plotting_test"]
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
