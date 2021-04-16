from math import isclose
import numpy as np
from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor
from plotting.data_processor import DataError
from plotting.plotter import Plotter
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import csv
import scipy.stats

plot = Plotter()

def single_experiment(host: str, task_type: str, database: str, tags: list = None, uuid: str = None):
    p = DataProcessor()

    if tags is not None:
        result = get_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags}})
    elif uuid is not None:
        result = get_experiment_data(host, task_type, results_db=database, uuid=uuid)
    else:
        return
    cost, confidence = result.get_cost_per_time()
    plt.plot(cost)
    plt.show()
    #plot.plot_cost_over_trials(p.get_monotonically_decreasing_cost(result.get_cost_per_trial()))


def average_experiment(host: str, task_type: str, database: str, tags: list, agent = None):
    p = DataProcessor()

    results = get_multiple_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags}})
    # cost = p.get_average_cost_over_time(results, 1500, True)
    cost, confidence = p.get_average_cost(results, True, 1, agent)
    plt.plot(cost)
    plt.ylim([0,2.5])
    plt.show()


def plot_experiment(host: str, task_type: str, database: str, tags: list):
    p = DataProcessor()
    legend = []

    for i in range(10):
        try:
            tags_tmp = tags.copy()
            tags_tmp.append("n" + str(i+1))

            result = get_experiment_data(host, task_type, results_db=database, filter={"meta.tags": {"$all": tags_tmp}})
            plt.plot(p.get_monotonically_decreasing_cost(result.get_cost_per_trial()))
            legend.append("n" + str(i + 1))
        except DataNotFoundError as e:
            print("Data not found for tags: " + str(tags_tmp))
            pass

    plt.legend(legend)
    plt.show()


def agent_learning(tags, hosts = ["collective-panda-002.local"]):
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
            axes[i, j].set_ylim(0, 10)
            axes_casr[i, j].set_ylim(0, 1500)
            axes[i, j].grid()
            axes[i, j].tick_params(axis="both", which="both", length=0)
            axes[i, j].set_title(tasks[i * n_rows + j], y=1.0, pad=-14)
            legend = []
            try:
                tags = ["transfer_learning", tasks[i * n_rows + j]]
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
                base_casr = np.insert(base_casr, 0, 0)

                for k in range(1, len(base_casr)):
                    base_casr[k] += base_casr[k - 1]

                axes[i, j].plot(base_cost, linestyle="dashed", zorder=2, linewidth=4)
                axes_casr[i, j].plot([0, len(base_casr)], [0, len(base_casr)], color="black", linestyle="dashed")
                axes_casr[i, j].plot(base_casr, linestyle="dashed", zorder=2, linewidth=4)
                legend = ["Optimal CASR", tasks[i * n_rows + j]]
            except (DataNotFoundError, DataError):
                print("Base cost for task " + tasks[i] + " not found.")
                continue
            for t in range(len(tasks)):
                try:
                    tags = ["transfer_learning", tasks[i * n_rows +j], "from_" + tasks[t]]
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
                    casr_matrix[i * n_rows + j][t] = np.sum(casr)/np.sum(base_casr)

                    speedup_matrix[i * n_rows + j][t] = calculate_speedup(base_cost, cost)
                    axes[i, j].plot(cost, zorder=1, color = task_colors[t])
                    axes_casr[i, j].plot(casr, zorder=1, color=task_colors[t])

                    legend.append("from_" + tasks[t])
                except (DataNotFoundError, DataError):
                    pass

            axes[i, j].legend(legend, fontsize='x-small', loc=1)
            axes_casr[i, j].legend(legend, fontsize='x-small', loc='upper left')
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
        ax.set_xlabel("Time [s]", fontsize = 12)
        ax_casr.set_xlabel("Time [s]")
    ax.set_ylabel("Execution time [s]", fontsize = 12)
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

    es_matrix = np.hstack((header.reshape(-1,1), es_matrix))
    speedup_matrix = np.hstack((header.reshape(-1, 1), speedup_matrix))
    le_ratio_matrix = np.hstack((header.reshape(-1, 1), le_ratio_matrix))
    casr_matrix = np.hstack((header.reshape(-1, 1), casr_matrix))

    np.savetxt("es_matrix.csv", es_matrix, delimiter=",", fmt="%s")
    np.savetxt("speedup_matrix.csv", speedup_matrix, delimiter=",", fmt="%s")
    np.savetxt("ler_matrix.csv", le_ratio_matrix, delimiter=",", fmt="%s")
    np.savetxt("casr_matrix.csv", casr_matrix, delimiter=",", fmt="%s")
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


def calculate_speedup(base_cost: list, cost: list):
    confidences = np.linspace(0.02, 0.05, 8)
    speedup_sum = 0
    for c in confidences:
        index_thr_base_cost = find_convergence(base_cost, c)
        thr_base_cost = base_cost[index_thr_base_cost]
        index_thr_transfer_cost = np.where(cost < thr_base_cost)
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
    return value/2.54

def plot_ler_matrix():
    ler_matrix_csv = open('ler_matrix.csv', 'r')
    plots = csv.reader(ler_matrix_csv, delimiter=',')
    ler_matrx = np.zeros((9, 9))
    ler_matrix_sorted = np.zeros((9, 9))
    ler_matrix_tasks = np.zeros((9, 9))
    #bar_colors = ["blue", "red", "green", "yellow", "orange", "cyan", "pink", "saddlebrown", "lavender"]
    bar_colors = ["red", "green", "yellow", "orange", "cyan", "blueviolet", "black", "dimgrey", "lightgrey"]
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", "key_pad", "key_old", "key_hatch"]
    tasks_short = ["$t_1$", "$t_2$", "$t_3$", "$t_4$", "$t_5$", "$t_6$", "$t_7$", "$t_8$", "$t_9$"]
    cnt_row = 0

    for row in plots:
        if cnt_row == 0:
            cnt_row += 1
            continue
        for i in range(len(row)):
            if i == 0:
                continue
            ler_matrx[cnt_row-1, i-1] = float(row[i])
        ler_matrix_sorted[cnt_row-1] = np.sort(ler_matrx[cnt_row-1])
        ler_matrix_tasks[cnt_row - 1] = np.argsort(ler_matrx[cnt_row - 1])
        cnt_row += 1
 # single axes
    fig, ax = plt.subplots(num="fig_ler")
    fig.subplots_adjust(left=0,right=1,bottom=0,top=1)
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
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color = colors[row], label = legend)   
            else:
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color = colors[row])   
    handles, labels = ax.get_legend_handles_labels()
    _,labels, handles = zip(*sorted(zip(ler_matrix_tasks[0, :],labels, handles), key=lambda t: t[0]))
    fig.set_size_inches(cm2inch(30),cm2inch(10))
    fontsize = 12
    ax.set_xticks(x + len(tasks) * dimw / 2) 
    ax.set_xticklabels(tasks, fontsize=fontsize) 
    ax.set_ylim(0, 2.1)
    ax.set_yticks([0, 0.4, 0.8, 1.2, 1.6, 2]) 
    ax.grid(axis="y")
    ax.set_ylabel("LER [1]", fontsize=fontsize)
    ax.tick_params(labelsize=fontsize)
    legend = ax.legend(handles, labels, loc="upper left",title="knowledge sources", fontsize=fontsize-2)
    plt.setp(legend.get_title(), fontsize = fontsize-2)
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
            ler_matrx[cnt_row-1, i-1] = float(row[i])
        ler_matrix_sorted[cnt_row-1] = np.sort(ler_matrx[cnt_row-1])
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
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color = colors[row], label = legend)   
            else:
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color = colors[row])   
    handles, labels = ax.get_legend_handles_labels()
    _,labels, handles = zip(*sorted(zip(ler_matrix_tasks[0, :],labels, handles), key=lambda t: t[0]))
    fig.set_size_inches(cm2inch(30),cm2inch(10))
    fontsize = 12
    ax.set_xticks(x + len(tasks) * dimw / 2) 
    ax.set_xticklabels(tasks, fontsize=fontsize)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1]) 
    ax.set_ylim(0, 1.02)
    ax.grid(axis="y")
    ax.set_ylabel("ES []", fontsize=fontsize)
    legend = ax.legend(handles, labels, loc="upper left",title="knowledge sources", fontsize=fontsize-2)
    plt.setp(legend.get_title(), fontsize = fontsize-2)
    plt.tight_layout()
    fig.savefig('fig_es.png',  dpi=500)
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
            ler_matrx[cnt_row-1, i-1] = float(row[i])
        ler_matrix_sorted[cnt_row-1] = np.sort(ler_matrx[cnt_row-1])
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
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color = colors[row], label = legend)   
            else:
                bar = ax.bar(x[row] + col * (dimw + 0.02), y[row], dimw, color = colors[row])   
    handles, labels = ax.get_legend_handles_labels()
    _,labels, handles = zip(*sorted(zip(ler_matrix_tasks[0, :],labels, handles), key=lambda t: t[0]))
    fig.set_size_inches(cm2inch(30),cm2inch(10))
    fontsize = 12
    ax.set_xticks(x + len(tasks) * dimw / 2) 
    ax.set_xticklabels(tasks, fontsize=fontsize) 
    ax.set_yscale('log') 
    ax.grid(axis="y")
    ax.set_ylabel("speedup [s]", fontsize=fontsize)
    ax.tick_params(labelsize=fontsize)
    legend = ax.legend(handles, labels, loc="upper right",title="knowledge sources", fontsize=fontsize-2)
    plt.setp(legend.get_title(), fontsize = fontsize-2)
    plt.tight_layout()
    fig.savefig('fig_speedup.png',  dpi=500)
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


def knowledge_quality(tags, hosts = ["localhost"], legend = None):
    filter = {"meta.tags": tags}
    knowledge_mode = "global"
    # task_type = "insert_object"
    task_type = "benchmark_rastrigin"

    p = DataProcessor()

    results = []
    for host in hosts:
        results.extend(get_multiple_experiment_data(host, task_type, knowledge_mode, filter=filter))
    results = p.sort_over_time(results)

    print("number of results: ",len(results))

    distances = []
    for r in results:
        lowest_cost = r.get_lowest_cost()
        init_knowledge = r.knowledge
        if init_knowledge is None:
            init_knowledge = r.get_theta_per_trial()[0]  # take first trial if no initial knowledge available
        init_knowledge = p.dict_to_list(init_knowledge)
        best_theta = p.dict_to_list(r.get_best_theta())
        created_knowledge = get_multiple_knowledge_data(hosts[0],task_type,knowledge_mode,{"meta.knowledge_source": r.uuid, "meta.tags": tags})[0]
        created_theta = created_knowledge.get_theta()

        dist = np.linalg.norm(np.array(created_theta) - np.array(init_knowledge))
        distances.append(dist)
    plot.plot_knowledge_error(distances, legend)
        

def transfer_learning_parameters(filter, host, result_db = "transfer_all_v2"):
    #calculate the mean distance between optimas and their initial knowledges
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60", "key_pad", "key_old", "key_hatch"] #,"key_abus_e30", "key_pad", "key_old", "key_hatch"]
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
                                                    filter={"meta.tags":  tags})
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
                #optimum = r.get_best_theta_norm()
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

    header = np.array(["from_"+task for task in header])
    header = np.insert(header, 0, "")

    means_mtx = np.hstack((header.reshape(-1,1), means_mtx))
    stds_mtx = np.hstack((header.reshape(-1,1), stds_mtx))

    np.savetxt("optima_knowledge_distance_mean.csv", means_mtx, delimiter=",", fmt="%s")
    np.savetxt("optima_knowledge_distance_std.csv", stds_mtx, delimiter=",", fmt="%s")

def no_transfer_learning_parameters(filter, host):
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60"] #,"key_abus_e30", "key_pad", "key_old", "key_hatch"]
    p = DataProcessor()
    data = {}
    for task in tasks:
        data[task] = {}
        try:
            tags = ["transfer_learning", task]
            results = get_multiple_experiment_data(host, "insert_object",
                                                results_db="results_tl_base",
                                                filter={"meta.tags":  tags})
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
    tasks = ["cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40", "cylinder_50", "cylinder_60"] #,"key_abus_e30", "key_pad", "key_old", "key_hatch"]
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
                                                filter={"meta.tags":  tags})
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
        print(task," mean_distance: ",np.mean(optima_matrix))
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


def color_matrix(name = "es_matrix.csv"):
    from matplotlib import cm
    from matplotlib.colors import ListedColormap, LinearSegmentedColormap
    
    data = np.genfromtxt(name, delimiter=',')
    data = np.delete(data,0,0)  # deleting names
    data = np.delete(data,0,1)
    min_value = min(data.flatten())
    max_value = max(data.flatten())
    cmap = cm.get_cmap('turbo', (max_value-min_value)*100)
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
    results = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results", filter={"meta.tags": {"$all": tags}})
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

    plt.ylim([0,1])
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

    plt.legend(("Task_0_single", "Task_01_single", "Task_02_single", "Task_0_shared", "Task_01_shared", "Task_02_shared"))

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
    results = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results", filter={"meta.tags": {"$all": tags}})
    cost = data_processor.get_average_cost(results, True, episode_length)
    plt.plot(cost)


def add_plot_over_time(host: str, tags: list, data_processor: DataProcessor):
    results = get_multiple_experiment_data(host, "benchmark_rastrigin", results_db="ml_results", filter={"meta.tags": {"$all": tags}})
    cost, confidence = data_processor.get_average_cost_over_time(results, decreasing=True)
    plt.plot(cost)


def plot_stuff_1():
    p = DataProcessor()

    tags = ["collective_learning_experiment_multi"]
    results = get_multiple_experiment_data("collective-panda-007.local", "insert_object", results_db="ml_results", filter={"meta.tags": {"$all": tags}})
    agent = "collective-panda-008"
    cost = p.get_average_cost_over_time(results, 2000, True, agent)
    # cost = p.get_average_cost(results, True, 1, agent)
    plt.plot(cost)

    tags = ["transfer_learning", "cylinder_60"]
    results = get_multiple_experiment_data("collective-control-001.local", "insert_object", results_db="transfer_base_v2", filter={"meta.tags": {"$all": tags}})
    cost = p.get_average_cost_over_time(results, 2000, True)
    # cost = p.get_average_cost(results, True, 1)
    plt.plot(cost)

    plt.legend(("Shared","Single"))

    plt.ylim([0,1])
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
        results = get_multiple_experiment_data(host, skills[i], results_db="iros2021", filter={"meta.tags": {"$all": tags}})
        cost, confidence = p.get_average_cost_over_time(results, decreasing=True)
        cost = cost * 5
        axes[i].fill_between(np.linspace(0, len(cost), len(cost)), cost-confidence, cost+confidence*5, alpha=0.2)
        axes[i].plot(cost, linewidth=2)
        axes[i].plot([0, len(cost)], [5, 5],  color="black", linestyle="dashed")

        time = [expert[tags2[i]]["time"][0]]
        for j in range(1, len(expert[tags2[i]]["time"])):
            time.append(expert[tags2[i]]["time"][j] + time[j-1])

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
