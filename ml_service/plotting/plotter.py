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
            if self.axs.get(func.__name__,False): # if figure is already available
                logger.debug("Update existing plot "+str(func.__name__))
                plt.sca(self.axs[func.__name__])
            else:
                logger.debug("Create new plot "+str(func.__name__))
                fig, ax = plt.subplots(num=func.__name__)
                self.axs[func.__name__] = ax

            result = func(self,*args,**kwargs)

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
        if legend is not None:
            ax.legend()
        
    @plotter_management
    def plot_theta_changes(self):
        pass



        
