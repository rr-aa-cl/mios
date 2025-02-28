import matplotlib.pyplot as plt
import matplotlib
import os
import pickle
import numpy as np

list_block_1 = ["001", #"002", 
                "003", "004", "005", 
                "006", "007", "008", "044", 
                "011", "012"]
list_block_2 = ["043","013","014","015","016","042",
                "041",#"020",
                "021","022"]
list_U = ["023", "024", "025", "047"]#, "028", "029"] #, "026"


def find_length(arr):
    # l = arr.shape[0]
    r = 0
    for i in arr:
        r = r + 1
        if i > 0.65:
            pass
        else:
            break
    # print(r)
    return r

def psp():
    robots = list_block_1 + list_block_2 + list_U
    mean_list = []
    std_list = []
    for xx in robots:
        if os.path.isfile("data17/psp_data/" + xx + ".pickle"):
            with open("data17/psp_data/" + xx + ".pickle", "rb") as file:
                data = pickle.load(file)
                mean_list.append(data[0])
                std_list.append(data[1])            
        else:
            print("File missing: data17/psp_data/" + xx + ".pickle")
            mean_list.append(np.array([1]*50))
            std_list.append(np.array([0]*50))
    
    return mean_list, std_list

def cmaes():
    psp_mean, psp_std = psp()
    robots = list_block_1 + list_block_2 + list_U
    mean_list = []
    std_list = []
    
    labels = ["IEC (C7)", "Triangle (S)", "Hexagon (S)", "USB (loose)", "Triangle (M)", "Cylinder (S)", "Key (type 1)", "Plug (type F & loose)", "Audio Jack (3.5mm)", "IEC (C13)", "Cylinder (M)", "Hexagon (M)", "HDMI (tight)", "Key (type 2)", "Cylinder (L)", "Square (S)", "Hexagon (L)", "Square (M)", "Audio jack (6.35mm)", "USB (tight)", "Plug (type C)", "Key (type 3)", "Plug(type F & tight)", "HDMI (tight)", "Key (type 4)"]

    
    for xx in robots:
        if os.path.isfile("data17/cmaes_data/" + xx + ".pickle"):
            with open("data17/cmaes_data/" + xx + ".pickle", "rb") as file:
                data = pickle.load(file)
                mean_list.append(data[0])
                std_list.append(data[1])
                
            # file
            
        else:
            print("File missing: data17/cmaes_data/" + xx + ".pickle")
            mean_list.append(np.array([1]*50))
            std_list.append(np.array([0]*50))
            
    matplotlib.rc('font', family='DejaVu Serif')
    fig, axs = plt.subplots(5, 5, figsize=(15, 7), constrained_layout=True)

    # Loop through all subfigures to add content
    xlim = 200 # TODO
    for i in range(5):
        for j in range(5):
            id = 5*i+j
            length = find_length(mean_list[id])
            axs[i, j].plot(range(1, length+1), mean_list[id][:length], label="CMA-ES") # Example plot, replace with actual data
            axs[i, j].fill_between(range(1, length+1), mean_list[id][:length]+std_list[id][:length], mean_list[id][:length]-std_list[id][:length],alpha=0.3, color='#0065bd')
            # axs[i, j].set_title(robots[id])  # Set title for each subplot
            
            plength = find_length(psp_mean[id])
            axs[i, j].plot(range(1, plength+1), psp_mean[id][:plength], label="PSP") # Example plot, replace with actual data
            axs[i, j].fill_between(range(1, plength+1), psp_mean[id][:plength]+psp_std[id][:plength], psp_mean[id][:plength]-psp_std[id][:plength],alpha=0.3, color='orange')
            
            
            axs[i, j].set_ylim(0, 2.5)
            axs[i, j].set_xlim(0, xlim)
            
            if i < 4:
                axs[i, j].set_xticklabels([])
                # axs[i, j].set_xticks([])
            
            if j > 0:
                axs[i, j].set_yticklabels([])
                # axs[i, j].set_yticks([])
            axs[i, j].grid()
            axs[i, j].set_title(labels[id],fontsize=9)
                
                
    # plt.subplots_adjust(left=0.2, right=0.9, top=1, bottom=0.1)
    # plt.tight_layout()
    lines, labels = axs[0,0].get_legend_handles_labels()
    fig.legend(lines, labels, ncol=2, bbox_to_anchor=(0.98,1))
            #       loc = "upper right")
    # 
    fig.suptitle(" ", fontsize=20)
    fig.supylabel(" ")  
    fig.supxlabel(" ")  
    plt.savefig("benchmark.png", dpi=600)

if __name__ == '__main__':
    cmaes()