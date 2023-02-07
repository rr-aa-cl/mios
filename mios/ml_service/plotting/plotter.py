from functools import wraps
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import logging

logger = logging.getLogger("ml_service")


class Plotter:
    def __init__(self):
        logger.debug("Plotter initialized")
        self.axs = {}
    
    def plotter_management(func):
        @wraps(func)
        def wrapper(self, *args,**kwargs):
            print("plot function: ", func.__name__)
            
            if str(func.__name__) in self.axs: # if figure is already available
                logger.debug("Update existing plot "+str(func.__name__))
                plt.sca(self.axs[str(func.__name__)])
            else:
                logger.debug("Create new plot "+str(func.__name__))
                fig, ax = plt.subplots(num=func.__name__)
                self.axs[str(func.__name__)] = ax

            result = func(self,*args,**kwargs)
            print(func.__name__ in self.axs)
            plt.show(block=False)
            plt.pause(0.1)
            return result
        return wrapper

    @plotter_management
    def plot_cost_over_trials(self, cost):

        ax = plt.gca()
        ax.plot(cost)
        ax.set_xlabel("trials")
        ax.set_ylabel("cost")


    @plotter_management
    def plot_time_over_trials(self, time):
        ax = plt.gca()
        ax.plot(time)
        ax.set_xlabel("trials [1]")
        ax.set_ylabel("time [s]")
        ax.set_title("Time per Trial")

    @plotter_management
    def plot_learning_over_task(self,time,legend = None):
        ax = plt.gca()    
        ax.plot(time,np.linspace(1,len(time),len(time)),label=legend)
        ax.set_ylabel("task [1]")
        ax.set_xlabel("time [s]")
        ax.grid(True)
        if legend is not None:
            ax.legend()

    @plotter_management
    def plot_learning_over_task_conf(self,time,legend = None):
        ax = plt.gca()    
        ax.plot(time,np.linspace(1,len(time),len(time)),label=legend)
        ax.set_ylabel("task [1]")
        ax.set_xlabel("time [s]")
        ax.grid(True)
        if legend is not None:
            ax.legend()
    
    @plotter_management
    def plot_knowledge_error(self, errors, legend = None):
        ax = plt.gca()
        ax.plot(errors, label = legend)
        ax.set_xlabel("Task [1]")
        ax.set_ylabel("knowledge error [1]")
        ax.set_title("knowledge error = distance between initial knowledge and generated knowledge")
        ax.grid(b=True)
        ax.legend()


    def plot_parameter_similarity(self, data):
        fig, axs = plt.subplots(nrows=int(np.ceil(len(data)/2)),ncols=2, sharey='col')
        axs = axs.flatten()
        data_keys = list(data.keys())
        for i in range(len(data_keys)):
            task = data[data_keys[i]]
            mean_distances = []
            std_distances = []
            task_keys = list(task.keys())
            for source in task_keys:
                mean_distances.append(task[source]["mean_dist"])
                std_distances.append(task[source]["std_dist"])
            axs[i].bar(task_keys, mean_distances,width=0.15, yerr=std_distances, label= "parameter distance")  
            axs[i].set_ylabel("distance [1]")
            axs[i].set_title(data_keys[i])
            #no ticks for some axis:
            axs[i].set_xticklabels([])
            axs[i].set(ylim=(0.5,1.4))
        axs[-1].bar(task_keys, [0 for task in task_keys]) 
        axs[-1].set_xticklabels(task_keys, fontsize='x-small', rotation=30) 
        axs[-2].set_xticklabels(task_keys, fontsize='x-small', rotation=30) 
        plt.tight_layout()

    @plotter_management
    def plot_default_centroid_dist(self, data: dict):
        ax = plt.gca()
        data_keys = list(data.keys())
        mean_distances = []
        std_distances = []
        for task_name in data_keys:
            mean_distances.append(data[task_name]["default centroid"]["mean_dist"])
            std_distances.append(data[task_name]["default centroid"]["std_dist"])
        ax.bar(data_keys, mean_distances,width=0.4, yerr=std_distances, label= "parameter distance")
        ax.set_ylabel("distance [1]")
        ax.set_title("distances to default centroids")
        ax.set_xticklabels(data_keys, fontsize='x-small')
        #ax.set(ylim=(0.5,1.6))
    

    def plot_table(self, data: list, name: str = None):
        if name is not None:
            plt.figure(name)
        else:
            plt.figure
        n_rows = len(data)
        n_cols = len(data[0])
        row_labels = ["n"+str(i) for i in range(n_rows)]
        col_labels = ["n"+str(i) for i in range(n_cols)]
        cell_text = []
        for row in range(n_rows):
            cell_text.append(['%1.2f' %x for x in data[row]])
        plt.table(cellText=cell_text,
                    rowLabels=row_labels,
                    colLabels=col_labels, loc=(0,0), cellLoc='center')
        plt.title(name)
        plt.axis('off')
        plt.show(block=False)
        plt.pause(0.1)

    @plotter_management
    def plot_theta_changes(self):
        pass



        
