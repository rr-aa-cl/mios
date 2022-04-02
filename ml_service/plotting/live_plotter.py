import pymongo
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style

from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor

def live_plot(robots, tags):
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
    fig, axes = plt.subplots(n_rows, n_cols, sharex='col', sharey='row')
    if len(robots) > 1:
        axes = axes.reshape(-1)
    else:
        axes = [axes]
    plot_lines = []  # all 2D line objects representing the plotted data
    current_data_sets = []
    for i in range(len(robots)):
        axes[i].grid()
        axes[i].set_title(robots[i])
        line, = axes[i].plot([],[], lw=3, color=colors[i])
        plot_lines.append(line)
        current_data_sets.append({"x":[], "y":[]})  # keep track of current data



    def get_results( host: str, skill_class: str, tags: list):
            p = DataProcessor()
            try:
                data = get_multiple_experiment_data(host, skill_class, "ml_results", filter={"meta.tags": {"$all": tags}})
            except DataNotFoundError:
                print("DataNotFoundError: host", host, " skill_class: ", skill_class, " tags: ", tags)
                return False, False
            if len(data) == 1:
                results = data[0]
            if len(data) > 1:
                most_recent_time = 0
                results = Result
                for r in data:
                    if r.starting_time > most_recent_time:
                        most_recent_time = r.starting_time
                        results = r

            if len(results.trials) == 0:
                print("TrialsNotFound: host", host, " skill_class: ", skill_class, " tags: ", tags)
                return False, False
            cost, time = results.get_cost_per_time()
            cost_mon = p.get_monotonically_decreasing_cost(cost)
            return cost_mon, time

    #def init():  # only required for blitting to give a clean slate.
    #    return plot_lines

    def animate(data):
        for i in range(len(robots)):
            cost,time = get_results(robots[i],"insertion", tags)
            if cost == False:
                continue
            current_data_sets[i]["x"] = time
            current_data_sets[i]["y"] = cost

            plot_lines[i].set_data(current_data_sets[i]["x"], current_data_sets[i]["y"])
            plot_lines[i].axes.set_xlim(0,max(time))
            if cost[-1] < 1:
                plot_lines[i].axes.set_ylim(0,1)
            else:
                plot_lines[i].axes.set_ylim(0,max(cost))
            
        return plot_lines

    def data_gen():
        steps = range(1,101)
        for i in steps:
            yield [x for x in range(1,i+1)], [x*x for x in range(1,i+1)]


    ani = animation.FuncAnimation(fig, animate, interval=1000) #, init_func=init, save_count=50, data_gen
    plt.show()
