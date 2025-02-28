import pymongo
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.image as mpimg
from xmlrpc.client import ServerProxy
from socket import gaierror

from matplotlib import style

from plotting.data_acquisition import *
from plotting.data_processor import DataProcessor


def demo_plot(robots):
    show_image = True
    try:
        img = mpimg.imread('plotting/panda.png')
        print(img.shape)
        height, width = img.shape[0], img.shape[1]
    except FileNotFoundError:
        show_image = False
    #imgplot = plt.imshow(img)
    #plt.show()

    robots = robots  # ["collective-panda-001.local", "collective-panda-002.local", "collective-panda-003.local", "collective-panda-009.local"]
    robot_names = ["prime-robot"]
    robot_names.extend(["robot-"+str(n+1) for n in range(len(robots))])
    cmap = plt.get_cmap('gist_rainbow')
    colors = [cmap(i) for i in np.linspace(0, 1, len(robots))]
    # calculating number of couloms:
    if len(robots) <= 24:
        n_cols = 4
    if len(robots) <= 12:
        n_cols = 4
    if len(robots) <= 6:
        n_cols = 2
    if len(robots) <= 3:
        n_cols = 2
    n_rows = int(np.ceil(len(robots)/n_cols))
    fig, axes = plt.subplots(n_rows, n_cols)  #, sharex='col', sharey='row'
    if n_rows > 1:
        axes = axes.reshape(-1)
    else:
        axes = axes#[axes]
    textboxes = []  # all 2D line objects representing the plotted data
    print(axes[0],axes[1])
    servers = []
    for i in range(len(robots)):
        servers.append(ServerProxy("http://" + robots[i] + ":8000", allow_none=True))
        axes[i].axis("off")
        axes[i].set_title(robot_names[i])
        if show_image:
            axes[i].imshow(img)
            textboxes.append(axes[i].text(width/2, height/2, "Not Ready", fontsize=24, ha='center', va='center', color="red"))
        else:
            t = axes[i].text(.5, .5, "Not Ready", fontsize=14, ha='center', va='center')
        textboxes.append(axes[i].text(0.5, 0.5, "Not Ready", fontsize=24, ha='center', va='center', color="red"))
        textboxes[-1].set_animated(True)
        #line, = axes[i].plot([],[], lw=3, color=colors[i])
        #plot_lines.append(line)
        #current_data_sets.append({"x":[], "y":[]})  # keep track of current data
    if len(robots)%2 != 0:
        axes[-1]
        axes[-1].grid()
        axes[-1].set_title("Learning Curve")
        line, = axes[-1].plot([],[], lw=3, color="b")
        textboxes.append(line)
        #current_data_sets.append({"x":[], "y":[]})  # keep track of current data
    demo_publisher = ServerProxy("https://0.0.0.0:8008", allow_none=True)    
    print("here!")


    def get_results( host: str, s):
        try:
            status = s.status()
        except ConnectionRefusedError:
            print("connectionRefusedError")
            return "ConnectionError","black"
        except gaierror:
            print("gaierror")
            return  "ConnectionError","black"
        if "is_busy" in status:
            if status["is_busy"] == True:
                return "learning", "green"
        else:
            return "Not Ready", "red"
        if "current_task" in status:
            return status["current_task"], "blue"
        else:
            return "Not Ready", "red"

    def get_ml_results(robot):
        p = DataProcessor()
        try:
            results = get_multiple_experiment_data(robot, "insertion", "ml_results", filter={"meta.tags": {"$all": ["demo2"]}})
            #results = get_multiple_experiment_data("localhost", "benchmark_rastrigin", "ml_results", filter={"meta.tags": {"$all": ["unique_test_tag"]}})
        except DataNotFoundError:
            return False, False
        for r in results:
            #print(len(r.trials))
            if len(r.trials) == 0:
                return False, False
        cost_mon = list()
        costs = list()
        times = [0]
        for result in results:
            cost, time = result.get_cost_per_time()
            if cost == False:
                return False, False
            if time == False:
                return False, False
            costs.extend(cost)
            cost_mon = p.get_monotonically_decreasing_cost(costs)
            times.extend([t+times[-1] for t in time])
            print(times)
        times.pop(0)
        return cost_mon, times

    def get_demo_results(host="lcoalhost"):
        status = demo_publisher.status()
        if len(status.keys()) > 0:
            for key in status.keys():
                if status[key] == "learning":
                    status[key+"-color"] = "green"
                elif status[key][:4] == "tele":
                    status[key+"-color"] = "blue"
                else:#
                    status[key+"-color"] = "black"
        else:
            status = {}
            for r in robots:
                status[r] = "Not Connected"
                status[r+"-color"] = "red"
        return status
    #def init():  # only required for blitting to give a clean slate.
    #    return plot_lines

    def animate(data):
        # #  get_results:
        # for i in range(len(robots)):
        #     status_string, color = get_results(robots[i], servers[i])
        #     textboxes[i].set_text(status_string)
        #     print(status_string)
        #     textboxes[i].set_color(color)
    
        #  get_demo_results:
        status = get_demo_results()
        for key in status.keys():
            i = robots.index(key)
            textboxes[i].set_text(status[key])


        #get_ml_resutls
        for robot in robots:
            cost_mon, time = get_ml_results(robot)
            if cost_mon == False:
                continue
            if time == False:
                continue
            #print("time: ",len(time),"  cost: ",len(cost_mon))
            textboxes[-1].set_data(time, cost_mon)
            textboxes[-1].axes.set_xlim(0,max(time))
            if cost_mon[-1] < 1:
                textboxes[-1].axes.set_ylim(0,1)
            else:
                textboxes[-1].axes.set_ylim(0,max(cost_mon))

        return textboxes
            
    ani = animation.FuncAnimation(fig, animate, interval=4000) #, init_func=init, save_count=50, data_gen
    plt.show()
