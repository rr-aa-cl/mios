import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
import seaborn as sns

def sns_heatmap(i , m):
    """
    Function for generating transfer heatmap. M(i,j) refers to the transferring from task-i to task-j.

    Args:
        i (_type_): the index inside the m. m[i] is the data for generating heatmap.
        m (_type_): data 3D matrix
    """
    color_list = ["#0C0C11", "#313044", "#555775", "#879BA7", "#BCD4D4", "#F4F8F7"]

    # color_list.reverse()
    cmap = colors.ListedColormap(color_list)
    # bounds = [0, 0.4, 0.6, 0.8, 1, 2.5, 3.5]
    bounds = [0, -0.4, -0.6, -0.8, -1, -2.5, -3.5]
    bounds.reverse()
    
    # bounds = list(range(11))
    norm = colors.BoundaryNorm(bounds, cmap.N)   
    labels = ["IEC(C7)", "Triangle-1", "Hexagon-1", "USB-1", "Triangle-2", "Cylinder-1", "Key-1", "Plug(type F)-1", "Audio Jack\n(3.5mm)", "IEC(C13)", "Cylinder-2", "Hexagon-2", "HDMI-1", "Key-2", "Cylinder-3", "Square-1", "Hexagon-3", "Square-2", "Audio jack\n(6.35mm)", "USB-2", "Plug(type C)", "Key-3", "Plug(type F)-2", "HDMI-2", "Key-4"]


    plt.clf()
    # c = sns.color_palette("light:#006600", as_cmap=True)
    # sss = [ str(i) for i in range(625)]
    # sss = np.array(sss)
    # sss = sss.reshape(25,25)
    # print(sss.shape)
    tmp = np.array([["{:.2f}".format(value) if value!=3 else " " for value in row] for row in m[i-1]])

    
    ax = sns.heatmap(-m[i-1], linewidth=0.5, cmap=cmap, norm=norm, annot=tmp.astype(str), fmt="") #fmt="g"

    ax.set_xticklabels(labels, rotation=90)    
    ax.set_yticklabels(labels, rotation=0)  
    cbar = ax.collections[0].colorbar
    cbar.set_ticks(bounds)
    tick_str = [" ", "0.4: Perfekt", "0.6: Excellent", "0.8: Very good", "1: Good","2.5: Fair", "Unknown" ]
    tick_str.reverse()
    cbar.set_ticklabels(tick_str)   
    # ax.set_yticks([])  # Remove y labels
    # plt.title("Collective Learning Process")

    ax.set_title(f'Collective Knowledge transfermap')


fig, ax = plt.subplots(figsize=(16, 12))
# data = np.load("transfer_array.npy")
name = "collective_131023/transfermap"
data = np.load(name+".npy")
down_data = data[::5]
print(data[-1], "length: ", len(data))

# data = data[-5:]

num_frames =  np.size(down_data, axis = 0)  # Number of frames in the video
# num_frames = 100
ani = FuncAnimation(fig, sns_heatmap, frames=num_frames, fargs=(down_data,), repeat=False, interval=1)

# Save the animation as a video (replace 'animation.mp4' with your desired filename)
Writer = animation.writers['ffmpeg']
writer = Writer(fps=2, bitrate=1800)
ani.save(name+'.mp4', writer=writer,  progress_callback = lambda i, n: print(f'Progress {i/n}'))
