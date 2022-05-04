import pymongo
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style

from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor

from xmlrpc.client import ServerProxy
from xmlrpc.client import Fault
import socket

def live_plot(robots, tags):
    matplotlib.rcParams.update({'font.size': 22})

    tags = tags  # ["collective_experiment_shared","paper_run_1", "n3"]
    robots = robots  # ["collective-panda-001.local", "collective-panda-002.local", "collective-panda-003.local", "collective-panda-009.local"]
    cmap = plt.get_cmap('gist_rainbow')
    colors = [cmap(i) for i in np.linspace(0, 1, len(robots))]
    # calculating number of couloms:
    if len(robots) <= 24:
        n_cols = 4
    if len(robots) <= 12:
        n_cols = 3
    if len(robots) <= 6:
        n_cols = 2
    if len(robots) <= 3:
        n_cols = 1
    n_rows = int(np.ceil(len(robots)/n_cols))
    fig, axes = plt.subplots(n_rows, 2*n_cols)#, sharex='col', sharey='row')
    #if len(robots) > 1:
    #    axes = axes.reshape(-1)
    #else:
    #    axes = [axes]
    plot_lines = []  # all 2D line objects representing the plotted data
    current_data_sets = []
    for i in range(len(robots)):
        row = int(np.floor(2*i/(2*n_cols)))
        col = (i - row*2*n_cols)*2

        axes[row, col].grid()
        idx = robots[i].find("-")
        axes[row, col].set_title(robots[i][idx+1:])
        axes[row, col].set_xlabel("time [s]")
        axes[row, col].set_ylabel("execution time [s]")
        axes[row, col].set_ylim([0, 5])
        line, = axes[row, col].plot([],[], lw=5, color=colors[i])
        plot_lines.append(line)
        current_data_sets.append({"x":[], "y":[]})  # keep track of current data

        text = axes[row, col+1].text(0.1,0.5,"Robot offline")
        plot_lines.append(text)
        axes[row, col+1].spines['top'].set_visible(False)
        axes[row, col+1].spines['right'].set_visible(False)
        axes[row, col+1].spines['bottom'].set_visible(False)
        axes[row, col+1].spines['left'].set_visible(False)
        axes[row, col+1].get_xaxis().set_ticks([])
        axes[row, col+1].get_yaxis().set_ticks([])

    plt.tight_layout()



    def get_results( host: str, skill_class: str, tags: list):
            p = DataProcessor()
            first_id = 0
            try:
                data = get_multiple_experiment_data(host, skill_class, "ml_results", filter={"meta.tags": {"$all": tags}})
            except DataNotFoundError:
                print("DataNotFoundError: host", host, " skill_class: ", skill_class, " tags: ", tags)
                return [0], [0]
            if len(data) == 1:
                results = data[0]
            if len(data) > 1:
                most_recent_time = 0
                results = Result
                for r in data:
                    if r.starting_time > most_recent_time:
                        most_recent_time = r.starting_time
                        results = r
                if first_id == 0:
                    first_id = results.id

            if len(results.trials) == 0:
                print("TrialsNotFound: host", host, " skill_class: ", skill_class, " tags: ", tags)
                return [0], [0]         
            cost = []
            time = []         
            if results.id == first_id:
                cost_1, time_1 = results.get_cost_per_time()
                cost = cost_1
                time = time_1
            else:
                cost_2, time_2= results.get_cost_per_time()
                cost = cost_1+cost_2
                time = time_1 + time_2
            cost = [c * 5 for c in cost]
            for i in range(len(cost)):
                if cost[i] > 5.0:
                    cost[i] = 5.0
            cost_mon = p.get_monotonically_decreasing_cost(cost)
            return cost_mon, time

    #def init():  # only required for blitting to give a clean slate.
    #    return plot_lines

    def animate(data):
        for i in range(len(robots)):
            cost,time = get_results(robots[i],"insertion", tags)
            if cost == False:
                print("cost = false")
                continue
            print("len current_data_set_time: ",len(current_data_sets))
            current_data_sets[i]["x"] = time
            current_data_sets[i]["y"] = cost
            
            plot_lines[2*i].set_data(current_data_sets[i]["x"], current_data_sets[i]["y"])
            plot_lines[2*i].axes.set_xlim(0,max(time))

            idx = robots[i].find("-")

            with ServerProxy("http://" + robots[i] + ":8000", allow_none=True) as service_server:
                try:
                    busy = service_server.is_busy()
                    if busy:
                        plot_lines[2*i+1].set_text(robots[i][idx+1:]+"\n is learning.")
                    else:
                        plot_lines[2*i+1].set_text(robots[i][idx+1:]+"\n is ready.")
                except socket.timeout:
                    logger.error("base_service: global Database is not reachable!")
                except ConnectionRefusedError:
                    plot_lines[2*i+1].set_text(robots[i][idx+1:]+"\n is offline.")
                except Fault:
                    plot_lines[2*i+1].set_text(robots[i][idx+1:]+"\n is offline.")
            
        return plot_lines

    def data_gen():
        steps = range(1,101)
        for i in steps:
            yield [x for x in range(1,i+1)], [x*x for x in range(1,i+1)]


    ani = animation.FuncAnimation(fig, animate, interval=1000) #, init_func=init, save_count=50, data_gen
    plt.show()
