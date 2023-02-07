import numpy as np

def Ackley(p):
    
    #x=p['skills']['test_fun']['skill']['a'][0]
    #y=p['skills']['test_fun']['skill']['b'][0]
    #task_desc = np.array(p['task_desc']["desc"],dtype='float64')
    x = p[0]
    y = p[1]
    task_desc = [1,0,0]  # k,a,b

    #Ackley with k variable (variations):
    res = -20*np.exp(-0.2*np.sqrt(0.5*((x - task_desc[1]) ** 2 + (y - task_desc[2]) ** 2))) - np.exp(0.5 * (np.cos(task_desc[0] * (x - task_desc[1])) + (np.cos(task_desc[0] * (y - task_desc[2]))))) + np.exp(1) + 20

   # elif p["task_desc"]["function"] == "rastrigin":
   #     # Rastrigin function:
   #     res = 20 * task_desc[0] * (
   #     (x - task_desc[1]) ** 2 - 10 * task_desc[0] * math.cos(2 * (x - task_desc[1])) + (y - task_desc[2]) ** 2 - 10 *
   #     task_desc[0] * math.cos(2 * (y - task_desc[2])))  # task_desc[0]*
   # elif p["task_desc"]["function"] == "booth":
   #     # Booth function:(too difficult for learner_gradient)
   #     res = 1 / task_desc[0] * ((x + 2 * y - task_desc[1]) ** 2 + (2 * x + y - task_desc[2]) ** 2)
   # elif p["task_desc"]["function"] == "rosenbrock":
   #     #Rosenbrock function:
   #     res = 100/task_desc[0]*(y-x**2-task_desc[2])**2 + (x-task_desc[1])**2
   # elif p["task_desc"]["function"] == "sphere":
   #     # Sphere function:
   #     # 1/k*((x_1-a)+(x_2-b))
   #     res = 1 / task_desc[0] * (math.pow((x - task_desc[1]), 2) + math.pow((y - task_desc[2]), 2))
   # else:
   #     # Sphere function:
   #     # 1/k*((x_1-a)+(x_2-b))
   #     res = 1 / task_desc[0] * (math.pow((x - task_desc[1]), 2) + math.pow((y - task_desc[2]), 2))


    #new border at [-10,10]x[-10,10]
    result=dict()
    if abs(x)<10 and abs(y)<10:
        result["result"]=1
        result["cost_suc"]=res
        result["cost_err"]=0
    else:
        result["result"]=-1
        x_diff = 0 if abs(x)<10 else abs(x)#-10
        y_diff = 0 if abs(y)<10 else abs(y)#-10
        result["cost_err"]=100+x_diff+y_diff
        result["cost_suc"]=0

    result["constraints"]=[]
    response=dict()
    response["result"]=result
    print("input=",p," result=",res)
    return response


def Sphere(p):
    
    #x=p['skills']['test_fun']['skill']['a'][0]
    #y=p['skills']['test_fun']['skill']['b'][0]
    #task_desc = np.array(p['task_desc']["desc"],dtype='float64')
    x = p[0]
    y = p[1]
    task_desc = [1,0,0]  # k,a,b


    # 1/k*((x_1-a)+(x_2-b))
    res = 1 / task_desc[0] * ((x - task_desc[1])**2 + (y - task_desc[2])**2)


    #new border at [-10,10]x[-10,10]
    result=dict()
    if abs(x)<10 and abs(y)<10:
        result["result"]=1
        result["cost_suc"]=res
        result["cost_err"]=0
    else:
        result["result"]=-1
        x_diff = 0 if abs(x)<10 else abs(x)#-10
        y_diff = 0 if abs(y)<10 else abs(y)#-10
        result["cost_err"]=100+x_diff+y_diff
        result["cost_suc"]=0

    result["constraints"]=[]
    response=dict()
    response["result"]=result
    print("input=",p," result=",res)
    return response