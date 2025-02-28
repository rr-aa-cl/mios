import subprocess
from datetime import datetime
import socket
import time
import os

# current_time = datetime.now()
# time_string = current_time.strftime("%Y%m%d_%H%M%S")
# hostname = socket.gethostname() # .replace("-", "_") 
# name = hostname+ "__" + time_string + ".mp4"
# print(name)
# ffmpeg_command = [
#     'ffmpeg',
#     '-f', 'video4linux2',
#     '-framerate', '30',
#     '-video_size', '1920x1080',
#     '-i', '/dev/video4',
#     name
# ]

# ffmpeg_process = subprocess.Popen(ffmpeg_command)

# time.sleep(10)

# ffmpeg_process.terminate()



class VideoRecorder:
    def __init__(self, tag="", device='/dev/video4', output_dir='./v/'):
        self.tag = tag
        self.device = device
        self.output_dir = output_dir

    def start_recording(self):
        current_time = datetime.now()
        time_string = current_time.strftime("%Y%m%d_%H%M%S")
        hostname = socket.gethostname()
        folders = self.tag.split("/")
        folder = self.output_dir
        for f in folders[:-1]:
            folder = folder+f+"/"
        os.system("mkdir -p %s"% folder)
        self.name = folder+f"{folders[-1]}HH{hostname}HH{time_string}.mp4"
        
        # file = open('v/read.txt', 'w') 
        # file.write('Welcome to Geeks for Geeks') 
        # file.close() 
        
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'video4linux2',
            '-framerate', '30',
            '-video_size', '1920x1080',
            '-i', self.device,
            self.name,
            '-hide_banner', 
            '-loglevel', 'error'
        ]
        
        # ffmpeg_command = ['pwd']
        self.ffmpeg_process = subprocess.Popen(ffmpeg_command)

        return True
    
    def __del__(self):
        print("terminate")

    def stop_recording(self):
        if hasattr(self, 'ffmpeg_process') and self.ffmpeg_process.poll() is None:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
        

# r = VideoRecorder("xx")

# r.start_recording()
# time.sleep(5)
# r.stop_recording()
