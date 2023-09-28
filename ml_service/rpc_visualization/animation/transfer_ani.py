import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
import seaborn as sns



# def sns_heatmap(i , m):
#     color_list = ["#F08080","#E7F1E7","#D4E6D4","#BDD7BD","#A7CBA7","#8DBB8D","#78AE78","#5E9E5E","#479147","#308030","#197519","#016701"]
#     cmap = colors.ListedColormap(color_list)
#     # labels = ["task"+str(i) for i in range(1,26)]
#     labels = ["IEC(C7)", "Triangle-1", "Hexagon-1", "USB-1", "Triangle-2", "Cylinder-1", "Key-1", "Plug(type F)-1", "Audio Jack(3.5mm)", "IEC(C13)", "Cylinder-2", "Hexagon-2", "HDMI-1", "Key-2", "Cylinder-3", "Square-1", "Hexagon-3", "Square-2", "Audio jack(6.35mm)", "USB-2", "Plug(type C)", "Key-3", "Plug(type F)-2", "HDMI-2", "Key-4"]
#     # bounds = [1, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]
#     bounds = [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
#     norm = colors.BoundaryNorm(bounds, cmap.N)
#     plt.clf()
#     # c = sns.color_palette("light:#006600", as_cmap=True)
#     ax = sns.heatmap(m[i], linewidth=0.5, cmap=cmap, norm=norm, annot=True)

#     ax.set_xticklabels(labels, rotation=45)    
#     ax.set_yticklabels(labels, rotation=45)  
#     # ax.set_yticks([])  # Remove y labels
#     # plt.title("Collective Learning Process")

#     ax.set_title(f'Collective Learning Process')


def sns_heatmap(i , m):
    color_list = ["#E7F1E7","#D4E6D4","#BDD7BD","#A7CBA7","#8DBB8D","#78AE78","#5E9E5E","#479147","#308030","#197519","#016701"]
    color_list.reverse()
    cmap = colors.ListedColormap(color_list)
    bounds = [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
    # bounds = list(range(11))
    norm = colors.BoundaryNorm(bounds, cmap.N)    # labels = ["task"+str(i) for i in range(1,26)]
    labels = ["IEC(C7)", "Triangle-1", "Hexagon-1", "USB-1", "Triangle-2", "Cylinder-1", "Key-1", "Plug(type F)-1", "Audio Jack\n(3.5mm)", "IEC(C13)", "Cylinder-2", "Hexagon-2", "HDMI-1", "Key-2", "Cylinder-3", "Square-1", "Hexagon-3", "Square-2", "Audio jack\n(6.35mm)", "USB-2", "Plug(type C)", "Key-3", "Plug(type F)-2", "HDMI-2", "Key-4"]


    plt.clf()
    # c = sns.color_palette("light:#006600", as_cmap=True)
    ax = sns.heatmap(m[i], linewidth=0.5, cmap=cmap, norm=norm, annot=True, fmt=".2f") #fmt="g"

    ax.set_xticklabels(labels, rotation=90)    
    ax.set_yticklabels(labels, rotation=0)  
    cbar = ax.collections[0].colorbar
    cbar.set_ticks(bounds)
    # ax.set_yticks([])  # Remove y labels
    # plt.title("Collective Learning Process")

    ax.set_title(f'Collective Learning Process')
 


# Create a figure and axis
fig, ax = plt.subplots(figsize=(16, 12))
# data = np.load("transfer_array.npy")
name = "transfermap"
data = np.load(name+".npy")
print(data[0])

num_frames =  np.size(data, axis = 0)  # Number of frames in the video
ani = FuncAnimation(fig, sns_heatmap, frames=num_frames, fargs=(data,), repeat=False, interval=100)

# Save the animation as a video (replace 'animation.mp4' with your desired filename)
Writer = animation.writers['ffmpeg']
writer = Writer(fps=10, bitrate=1800)
ani.save(name+'.mp4', writer=writer)

# Show the animation (optional)
plt.show()
