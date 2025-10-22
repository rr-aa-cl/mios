import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
import seaborn as sns







def sum_plot(i, m):
    
    plt.clf()
    plt.plot(data[2,:i], data[0,:i], label = "collective learning")
    plt.plot(data[2,:i], data[1,:i], label = "isolated learning")
    plt.legend()
    plt.xlabel("Time (min)")
    plt.ylabel("Nr. of successful trials")


 


# Create a figure and axis
fig, ax = plt.subplots(figsize=(8, 6))
name = "sum"
cl = np.load("cl_sum.npy").astype(int)
iso = np.load("iso_sum.npy").astype(int)

num_frames =  np.size(cl, axis = 0)  # Number of frames in the video
t = np.array(list(range(num_frames)))/600
data = np.concatenate((np.expand_dims(cl, axis=0), np.expand_dims(iso, axis=0), np.expand_dims(t, axis=0)), axis=0)

ani = FuncAnimation(fig, sum_plot, frames=num_frames, fargs=(data,), repeat=False, interval=100)

# Save the animation as a video (replace 'animation.mp4' with your desired filename)
Writer = animation.writers['ffmpeg']
writer = Writer(fps=10, bitrate=1800)
ani.save(name+'.mp4', writer=writer, progress_callback = lambda i, n: print(f'Progress {i/n}'))

# Show the animation (optional)
# plt.show()

# **************************************************************************
# a = np.load("../tensorboard/heatmap_collective.npy")
# num_frames =  np.size(a, axis = 0)
# b = np.load("../tensorboard/heatmap_isolated.npy")[:num_frames]
# # num_frames =  np.size(data, axis = 0)

# cl = np.zeros((num_frames,))
# iso = np.zeros((num_frames,))

# for i in range(num_frames):
#     cl[i] = np.sum(a[i])
#     iso[i] = np.sum(b[i])

# np.save("cl_sum.npy", cl)
# np.save("iso_sum.npy", iso)
# **************************************************************************