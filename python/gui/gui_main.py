from tkinter import Tk, Label, Button, Entry, Checkbutton
from tkinter import ttk
import tkinter
import subprocess
import requests
import json
import ast


class MIOSGUI:
    def __init__(self, master):
        self.master = master
        master.title("MIOS GUI")

        # Connect
        self.b_connect = Button(master, text="Connect", command=self.connect)
        self.b_connect.grid(row=0, column=0)
        self.e_connect = Entry(master)
        self.e_connect.grid(row=0, column=1)

        # Start task
        self.l_start_task1 = Label(master, text="Task")
        self.l_start_task1.grid(row=1, column=1)
        self.l_start_task2 = Label(master, text="Parameters")
        self.l_start_task2.grid(row=1, column=2)
        self.b_start_task = Button(master, text="Start task", command=self.start_task)
        self.b_start_task.grid(row=2, column=0)
        self.e_start_task1 = Entry(master)
        self.e_start_task1.grid(row=2, column=1)
        self.e_start_task2 = Entry(master)
        self.e_start_task2.grid(row=2, column=2)

        # Stop task
        self.l_stop_task1 = Label(master, text="Nominal")
        self.l_stop_task1.grid(row=3, column=1)
        self.l_stop_task2 = Label(master, text="Success")
        self.l_stop_task2.grid(row=3, column=2)
        self.b_stop_task = Button(master, text="Stop task", command=self.stop_task)
        self.b_stop_task.grid(row=4, column=0)
        self.c_stop_task1 = ttk.Checkbutton(master)
        self.c_stop_task1.grid(row=4, column=1)
        self.c_stop_task2 = ttk.Checkbutton(master)
        self.c_stop_task2.grid(row=4, column=2)

        self.hostname = "tueirsi-nc-012.local"

    def connect(self):
        if self.ping_host(self.e_connect.get()) != 0:
            self.hostname = None
            print("Could not connect to " + self.e_connect.get())
        else:
            self.hostname = self.e_connect.get()
            print("Connected to " + self.e_connect.get())

    def start_task(self):
        if self.hostname is None:
            print("Not connected to MIOS.")
            return

        params = {
            'task_id': self.e_start_task1.get(),
            'queue_task': False,
            'parameters': ast.literal_eval(self.e_start_task2.get())
        }
        response = self.rpc_call("http://" + self.hostname + ":8383", "start_task", params)
        print(response)

    def stop_task(self):
        if self.hostname is None:
            print("Not connected to MIOS.")
            return

        print(self.c_stop_task1.state())
        params = {
            'nominal': True if "selected" in self.c_stop_task1.state() else False,
            'success': True if "selected" in self.c_stop_task2.state() else False
        }
        response = self.rpc_call('http://' + self.hostname + ':8383', 'stop_task', params)
        print(response)

    @staticmethod
    def rpc_call(url, method, params=None):
        headers = {'content-type': 'application/json'}
        if params is None:
            params = {None: None}

        payload = {
            u"method": method,
            u"params": params if params else u"",
            u"jsonrpc": u"2.0",
            u"id": 0,
        }
        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers).json()
        except requests.Timeout:
            print('Timeout, server has terminated or does not exist.')
            response = None
        except requests.ConnectionError:
            print('Connection error, target url not reachable.')
            response = None

        return response

    @staticmethod
    def ping_host(hostname):
        return subprocess.call('ping -c 2 ' + hostname, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


root = Tk()
my_gui = MIOSGUI(root)
root.mainloop()
