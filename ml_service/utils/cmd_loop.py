from utils.helper_functions import Task
from utils.ws_client import *
from threading import Thread
import time

class CMDLoop():
    def __init__(self, cmd):
        self.keep_running = False
        self.thread = None
        self.port = None
        self.cmd = cmd
        self.sleep = False
        self.agent = self.cmd["agent"]
        if "sleep" in cmd:
            self.sleep = cmd["sleep"]
        if "port" in cmd:
            self.port = cmd["port"]
        else:
            self.port = 13000
        self.skills = cmd["skills"]

    def _execute_loop(self):
        t = Task(self.agent, self.port)
        for i in range(0,100):
            for skill in self.skills:
                t.add_skill(skill[0]+"-"+str(i),skill[1],skill[2])
        #t.add_skill("hold","HoldPose",self.hold_context)
        while(self.keep_running):
            t.start(queue=False)
            t.wait(timeout=1000)
            if self.sleep:
                time.sleep(self.sleep)
        return True
            
    def stop(self):
        self.keep_running = False
        call_method(self.agent,self.port,"stop_task")
        self.thread.join()

    def start(self):
        self.keep_running = True
        self.thread = Thread(target=self._execute_loop)
        self.thread.start()