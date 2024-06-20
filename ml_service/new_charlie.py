from copy import deepcopy
import time
import random

from problem_definition.domain import Domain
from run_experiments import *

tasks = {   
            "collective-007.rsi.ei.tum.de":["D_022","D_011"],
            "collective-006.rsi.ei.tum.de":["D_002", "D_001", "D_021"],
            "collective-011.rsi.ei.tum.de":["D_010", "D_015","D_023"],
        }   

todos = deepcopy(tasks)
dos = []
threads = []


def update_todos(x):
    todos[x].pop(0)
    if len(todos[x]) == 0:
        del todos[x]
    print(todos)
    
def doing(x):

    dos.append(x)
    print("start ", todos[x][0])
    update_todos(x)
    time.sleep(random.randint(1, 20))
    print("stop ", x)
    dos.remove(x)

n_agent = 2


while True:
    time.sleep(1)
    if len(todos) == 0:
        if sum([t.is_alive() for t in threads]) == 0:
            break
    
    time.sleep(1)
    i = 0
     
    while len(dos) < n_agent and len(todos) > 0:
        if i+1 > len(todos):
            break
        
        x = list(todos.keys())[i]
        if  x in dos:
            # print(x + " is busy now")
            i = i + 1
        
        else:
            threads.append(Thread(target=doing, args=(x,)))
            threads[-1].start()
            

