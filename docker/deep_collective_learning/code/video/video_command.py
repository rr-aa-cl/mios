import subprocess
from datetime import datetime
import socket
import time

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
    def __init__(self, device='/dev/video4', output_dir='./'):
        self.device = device
        self.output_dir = output_dir

    def start_recording(self):
        current_time = datetime.now()
        time_string = current_time.strftime("%Y%m%d_%H%M%S")
        hostname = socket.gethostname()
        self.name = f"{hostname}HH{time_string}.mp4"
        
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'video4linux2',
            '-framerate', '30',
            '-video_size', '1920x1080',
            '-i', self.device,
            self.name
        ]

        self.ffmpeg_process = subprocess.Popen(ffmpeg_command)
    
    def __del__(self):
        print("terminate")

    def stop_recording(self):
        if hasattr(self, 'ffmpeg_process') and self.ffmpeg_process.poll() is None:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
        

recorder = VideoRecorder()
recorder.start_recording()

time.sleep(10)  
recorder.stop_recording()