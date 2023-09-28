import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
import seaborn as sns



# Function to generate a heatmap (replace this with your heatmap generation logic)
def generate_heatmap(frame_number):
    data = np.random.rand(5, 5)  # Replace with your heatmap data
    ax.clear()
    sns.heatmap(data, annot=True, fmt=".2f", cmap="YlGnBu", cbar=False, ax=ax)
    ax.set_title(f'')


def sns_heatmap(i , m):
    color_list = ["#E7F1E7","#D4E6D4","#BDD7BD","#A7CBA7","#8DBB8D","#78AE78","#5E9E5E","#479147","#308030","#197519","#016701"]
    cmap = colors.ListedColormap(color_list)
    bounds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100]
    # bounds = list(range(11))
    norm = colors.BoundaryNorm(bounds, cmap.N)
    plt.clf()
    # c = sns.color_palette("light:#006600", as_cmap=True)
    labels = np.array([["IEC(C7)", "Triangle-1", "Hexagon-1", "USB-1", "Triangle-2"], 
                       ["Cylinder-1", "Key-1", "Plug\n(type F)-1", "Audio Jack\n(3.5mm)", "IEC(C13)"],
                       ["Cylinder-2", "Hexagon-2", "HDMI-1", "Key-2", "Cylinder-3"],
                       ["Square-1", "Hexagon-3", "Square-2", "Audio jack\n(6.35mm)", "USB-2"],
                       ["Plug\n(type C)", "Key-3", "Plug\n(type F)-2", "HDMI-2", "Key-4"]])
    
    ax = sns.heatmap(m[i], linewidth=0.5, cmap=cmap, norm=norm, annot=labels, fmt="", annot_kws={"fontsize":8})
    ax.set_xticks([])  # Remove x labels
    ax.set_yticks([])  # Remove y labels
    cbar = ax.collections[0].colorbar
    cbar.set_ticks([0,1, 2, 3, 4, 5, 6, 7, 8,9,10, 100])
    # plt.title("Collective Learning Process")

    ax.set_title(f'Collective Learning Process')

 


# Create a figure and axis
fig, ax = plt.subplots(figsize=(8, 6))
name = "heatmap"
data = np.load(name+".npy").astype(int)
print(data[0])
num_frames =  np.size(data, axis = 0)  # Number of frames in the video
ani = FuncAnimation(fig, sns_heatmap, frames=num_frames, fargs=(data,), repeat=False, interval=100)

# Save the animation as a video (replace 'animation.mp4' with your desired filename)
Writer = animation.writers['ffmpeg']
writer = Writer(fps=10, bitrate=1800)
ani.save(name+'.mp4', writer=writer)

# Show the animation (optional)
plt.show()
