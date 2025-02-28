from deep_learning.agents.ppo import PPO
from deep_learning.agents.sac import SAC
from deep_learning.agents.ddpg import DDPG
from deep_learning.utils.utils import Dict
from configparser import ConfigParser
from desk.mongodb_client import MongoDBClient
from torch.utils.tensorboard import SummaryWriter
from datetime import datetime
import xmlrpc.client
import subprocess
import requests
import pickle
import socket
import numpy as np
import torch
import copy
import math
import time
import os
from tqdm import tqdm

import asyncio
from desk.mongodb_client import MongoDBClient

tasks={'collective-001.rsi.ei.tum.de': 'B_002_IEC-C7',
 'collective-003.rsi.ei.tum.de': 'D_028',
 'collective-004.rsi.ei.tum.de': 'D_020',
 'collective-005.rsi.ei.tum.de': 'D_027',
 'collective-006.rsi.ei.tum.de': 'D_021',
 'collective-007.rsi.ei.tum.de': 'D_022',
 #'collective-008.rsi.ei.tum.de': '008_left',
 'collective-033.rsi.ei.tum.de': 'D_023',
 'collective-035.rsi.ei.tum.de': 'C_007',
 'collective-043.rsi.ei.tum.de': 'B_013',
 'collective-013.rsi.ei.tum.de': 'C_011',
 'collective-014.rsi.ei.tum.de': 'B_016',
 #'collective-015.rsi.ei.tum.de': 'C_025',
 'collective-016.rsi.ei.tum.de': 'A_026_cylinder_30',
 #'collective-042.rsi.ei.tum.de': 'mercedes_star',
 'collective-041.rsi.ei.tum.de': 'A_009_hexagon-3',
 'collective-021.rsi.ei.tum.de': 'B_RS-232',
 #'collective-022.rsi.ei.tum.de': 'C_009',
 'collective-023.rsi.ei.tum.de': 'C_014',
 'collective-024.rsi.ei.tum.de': 'B_014_CN',
 'collective-025.rsi.ei.tum.de': 'A_025_heart',
 'collective-026.rsi.ei.tum.de': 'A_016_cross-1',
 'collective-047.rsi.ei.tum.de': 'B_010_plugF-2'}

modelKnowledge0={'mode':0,
                'scaling':[1,1,1,1,1,1,1],
                'actionLimits':[[-1,1],[-1,1],[-1,1],[-1,1],[-1,1],[-1,1],[-1,1]],
                'sigmaScaling':1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}

modelKnowledge01={'mode':0,
                'scaling':[2,2,2,2,2,2,2],
                'actionLimits':[[-2,2],[-2,2],[-2,2],[-2,2],[-2,2],[-2,2],[-2,2]],
                'sigmaScaling':1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}



modelKnowledge1={'mode':1,
                'scaling':[1,1,1,1,1,1],
                'actionLimits':[[-1,1],[-1,1],[-1,1],[-1,1],[-1,1],[-1,1]],
                'sigmaScaling':1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}
#todo
modelKnowledge2={'mode':1,
                'scaling':[1,1,1,1,1,1],
                'actionLimits':[[-3,3],[-3,3],[-3,3],[-3,3],[-3,3],[-3,3]],
                'sigmaScaling':1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}
#todo
modelKnowledge3={'mode':1,
                'scaling':[1,1,1,1,1,1],
                'actionLimits':[[-3,3],[-3,3],[-3,3],[-3,3],[-3,3],[-3,3]],
                'sigmaScaling':0.1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}

modelKnowledge4={'mode':2,
                'scaling':[0.005,0.005,0.005,0.005,0.005,0.005,0.005],
                'actionLimits':[[-0.005,0.005],[-0.005,0.005],[-0.005,0.005],[-0.005,0.005],[-0.005,0.005],[-0.005,0.005],[-0.005,0.005]],
                'sigmaScaling':1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}

# modelKnowledge4={'mode':2,
#                 'scaling':[0.01,0.01,0.01,0.01,0.01,0.01,0.01],
#                 'actionLimits':[[-0.01,0.01],[-0.01,0.01],[-0.01,0.01],[-0.01,0.01],[-0.01,0.01],[-0.01,0.01],[-0.01,0.01]],
#                 'sigmaScaling':1,
#                 'graspOrientation':[1,0,0,0,1,0,0,0,1]}


modelKnowledge5={'mode':3,
                'scaling':[0.0004,0.0004,0.0004,0.0004,0.0004,0.0004],
                'actionLimits':[[-0.0004,0.0004],[-0.0004,0.0004],[-0.0004,0.0004],[-0.0004,0.0004],[-0.0004,0.0004],[-0.0004,0.0004]],
                'sigmaScaling':1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}
#todo
modelKnowledge6={'mode':3,
                'scaling':[0.001,0.001,0.001,0.001,0.001,0.001],
                'actionLimits':[[-0.001,0.001],[-0.001,0.001],[-0.001,0.001],[-0.001,0.001],[-0.001,0.001],[-0.001,0.001]],
                'sigmaScaling':1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}
#todo
modelKnowledge7={'mode':3,
                'scaling':[0.001,0.001,0.001,0.001,0.001,0.001],
                'actionLimits':[[-0.001,0.001],[-0.001,0.001],[-0.001,0.001],[-0.001,0.001],[-0.001,0.001],[-0.001,0.001]],
                'sigmaScaling':0.1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}

learningParams= {'architecture':'sac',
                'epochs':500,
                'train':True,
                'experiment_ID': 0,
                'number_of_experiments': 5,
                'saveInterval':100,
                'frequency': 25,
                'taskID':0,
                'logging':True,
                'maxTime':5,
                'load':'no'}
# tags = []
# for key in learningParams.keys():
#     tags.append(key+"="+learningParams[key])
tags=[learningParams['architecture']]
#tags = ["sac"]


def get_ip_address(hostname):
    try:
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.gaierror:
        return "Hostname could not be resolved."

class CollectiveDeepReinforcementLearner():
    def __init__(self,learning_params,model_knowledge):
        self.learning_params=learning_params
        self.model_knowledge=model_knowledge
        self.architecture=learning_params['architecture']
        self.logging=learning_params['logging']
        self.loadExistingNetwork=learning_params['load']
        self.saveInterval=learning_params['saveInterval']
        self.timeoutTime=120
        self.bars=[]
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print("Device: ",self.device)
        self.tags = tags

        if self.model_knowledge['mode']==0:
            self.interface='Torque'
            self.end2end=True
        elif self.model_knowledge['mode']==1:
            self.interface='Wrench'
            self.end2end=False
        elif self.model_knowledge['mode']==2:
            self.interface='JointPose'
            self.end2end=True
        elif self.model_knowledge['mode']==3:
            self.interface='Twist'
            self.end2end=False

        parser = ConfigParser()
        parser.read('deep_learning/config.ini')
        self.agent_args = Dict(parser,self.architecture)
        self.mongo_client = MongoDBClient()
        iteration = 1
        while len(self.mongo_client.read("deep_ml_results", "insertion", {"meta.tags": self.tags+["iteration_"+str(iteration)]})) >= 1:
            iteration += 1
        self.tags.append("iteration_"+str(iteration))

    def initializeLocalLearners(self):
        def ping_hosts(tasks):
            reachable_hosts = []
            unreachable_hosts = []
            working_IPs=[]
            for task in tasks:
                result = subprocess.run(['ping', '-c', '1', '-W', '1', str(task)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    working_IPs.append(task.split(".")[0])
                    reachable_hosts.append(task.split(".")[0])
                else:
                    unreachable_hosts.append(task.split(".")[0])
            return working_IPs, reachable_hosts, unreachable_hosts


        working_Hosts,reachable, unreachable = ping_hosts(tasks)
        print(working_Hosts)
        print("Reachable hosts:", reachable)
        print("Unreachable hosts:", unreachable)


        self.robotLearningInstances=[]
        i=0
        for host in working_Hosts:
            try:
                RPC_SERVER_URL = "http://"+host+":9000"

                response = requests.get(RPC_SERVER_URL)
                response_time = response.elapsed.total_seconds()
                print("Response time:", response_time, "seconds")

                learnerProxy = xmlrpc.client.ServerProxy("http://"+host+":9000")
                if(learnerProxy.running()==True):
                    IP=get_ip_address(host)
                    if(learnerProxy.setModelKnowledge(self.model_knowledge)==True and
                    learnerProxy.setLearningParams(self.learning_params)==True and
                    learnerProxy.setID(host,IP)==True):
                        self.robotLearningInstances.append([host,IP])
                        print("Initialization of "+host+" successful!")
                        #self.bars.append(tqdm(total=self.learning_params['epochs'],desc=host, position=i, leave=True, bar_format='{desc}:{bar}|{n_fmt}') )
                        i+=1
                    else:
                        print("Initialization of "+host+" failed!")
            except:
                print("Initialization of "+host+" failed!")
        print("Finished Initialization!")

    async def rpc_call_to_learner(self,learnerProxy,index):
        host,IP=self.robotLearningInstances[index]
        task=self.loop.run_in_executor(None, getattr(learnerProxy, "learning"))
        try:
            startTime=time.time()
            await asyncio.wait_for(task,self.timeoutTime)
            #print(host, time.time()-startTime)
            self.conFails[index]=0
        except asyncio.TimeoutError:
            print(host,learnerProxy," did not respond")
            self.conFails[index]+=1
        finally:
            try:
                learnerProxy("close")()
                return index
            except Exception as e:
                print(f"Failed to close connection for {learnerProxy}: {e}")
                return index
        return index

    async def learning_loop(self,learningInstances,callback):
        self.learningTasks=set()
        index=0
        for host,IP in learningInstances:
            self.mongo_client.write("deep_ml_results","insertion",{"meta":{"learningInstance":host,
                                                                           "starting_time":time.time(),
                                                                           "tags": self.tags+[host],
                                                                           "learning_params": self.learning_params,
                                                                           "model_knowledge":self.model_knowledge,
                                                                           "architecture":self.architecture,
                                                                           "device":self.device,
                                                                           "end2end":self.end2end,
                                                                           "interface":self.interface}})  # create db entry
            learnerProxy = xmlrpc.client.ServerProxy("http://"+host+":9000")
            call_task = asyncio.create_task(self.rpc_call_to_learner(learnerProxy,index))
            self.learningTasks.add(call_task)
            index+=1

        while len(self.learningTasks)>0:
            done, pending=await asyncio.wait(self.learningTasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                try:
                    index=task.result()
                    isFinished=callback(index)
                    host,IP=self.robotLearningInstances[index]
                    if isFinished==False:
                        del learnerProxy
                        learnerProxy=xmlrpc.client.ServerProxy("http://"+IP+":9000")
                        if self.conFails[index]<5:
                            call_task = asyncio.create_task(self.rpc_call_to_learner(learnerProxy,index))
                            self.learningTasks.add(call_task)
                    else:
                        mongo_data = self.mongo_client.read("deep_ml_results","insertion",{"meta.tags":self.tags+[host]})
                        if mongo_data:
                            mongo_data = mongo_data[0]
                            mongo_data["meta"]["ending_time"] = time.time()
                            self.mongo_client.update("deep_ml_results","insertion",{"meta.tags":self.tags+[host]},mongo_data)
                except:
                    pass
                    
            self.learningTasks-=done
    
    def learning_callback(self,learner_index):
        host,IP=self.robotLearningInstances[learner_index]
        learnerProxy=xmlrpc.client.ServerProxy("http://"+IP+":9000")
        #1. get new trial data
        new_transitions=learnerProxy.getNewExperimentData()
        trialResult=learnerProxy.getTrialResult()
        self.learningLog[learner_index].append(trialResult)
        mongo_data = self.mongo_client.read("deep_ml_results","insertion",{"meta.tags":self.tags+[host]})
        if mongo_data:
            mongo_data = mongo_data[0]
            mongo_data["n"+str(len(self.learningLog[learner_index])+1)] = {"success":trialResult[0], "time":trialResult[1]}
            self.mongo_client.update("deep_ml_results","insertion",{"meta.tags":self.tags+[host]},mongo_data)
        #2. append data to agent
        for transition in new_transitions:
            self.agents[learner_index].put_data(transition) 
        #3. train model -> improve!
        #print(self.agents[learner_index].data.data_idx)
        if self.agents[learner_index].data.data_idx > 1024: #self.agent_args.learn_start_size: 
            startTime=time.time()
            for i in range(math.ceil(self.learning_params['maxTime']*self.learning_params['frequency']/4)):
                self.agents[learner_index].train_net(self.agent_args.batch_size*4, self.epochs[learner_index])
            print(self.epochs[learner_index], host, "Training time: ",time.time()-startTime)
        else:
            pass
            #print(host, "Insufficient samples: ",self.agents[learner_index].data.data_idx)
        #4. update weights
        state_dict_cpu = {k: v.cpu() for k, v in self.agents[learner_index].state_dict().items()}
        model_bytes = pickle.dumps(state_dict_cpu)
        if learnerProxy.setModelWeights(xmlrpc.client.Binary(model_bytes))==True:
            pass
        else:
            print("Transfer of weights to "+host+" failed!")   

        #5. store weights if needed
        self.epochs[learner_index]+=1
        if self.epochs[learner_index]%self.saveInterval==0:
            self.storedNetworkWeights[learner_index].append(copy.deepcopy(self.agents[learner_index].state_dict()))     
        #self.bars[learner_index].update(1)
        #7. start new learning epoch
        if self.epochs[learner_index]<self.learning_params['epochs']:
            return False
        else:
            return True

    def saveExperimentData(self,path):

        #create folder
        i=1
        folder_name = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(path+"/"+folder_name):
            os.makedirs(path+"/"+folder_name)

        while os.path.exists(path+"/"+folder_name+"/"+str(i)):
            i+=1

        os.makedirs(path+"/"+folder_name+"/"+str(i))
        #save experiment results
        with open(path+"/"+folder_name+"/"+str(i)+'/experiment_result.pkl', 'wb') as f:
            pickle.dump(self.learningLog, f)

        #save network weights
        os.makedirs(path+"/"+folder_name+"/"+str(i)+"/network_weights")

        print(len(self.storedNetworkWeights))

        for j in range(len(self.robotLearningInstances)):
            host,IP=self.robotLearningInstances[j]
            os.makedirs(path+"/"+folder_name+"/"+str(i)+"/network_weights/"+host)   
            print(host,len(self.storedNetworkWeights[j]))
            for k in range(len(self.storedNetworkWeights[j])):         
                torch.save(self.storedNetworkWeights[j][k],path+"/"+folder_name+"/"+str(i)+"/network_weights/"+host+"/"+str((k+1)*self.saveInterval))
               # mongo_data["n"+str(k+1)]["weights"] = self.storedNetworkWeights[j]

        #save experiment parameters                
        experiments_params = {'learning_params': self.learning_params, 'model_knowledge': self.model_knowledge}
        with open(path+"/"+folder_name+"/"+str(i)+'/experiments_params.pkl', 'wb') as f:
            pickle.dump(experiments_params, f)
        with open(path+"/"+folder_name+"/"+str(i)+'/experiments_params.txt', 'w') as f:
            f.write(str(experiments_params))

    def learning(self):
        #initialize state size
        if self.end2end==False:
            action_dim = 6
            state_dim = 18
        else:
            action_dim = 7
            state_dim = 21
        #initialize data logging and networks
        self.summaryWriters=[]
        self.agents=[]
        self.storedNetworkWeights=[]
        self.epochs=[]
        self.learningLog=[]
        self.conFails=[]
        for host,IP in self.robotLearningInstances:
            if self.logging==True:
                writer = SummaryWriter()
            else:
                writer = None

            self.summaryWriters.append(writer)

            if self.architecture == 'ppo' :
                agent = PPO(writer, self.device, state_dim, action_dim, self.agent_args)
            elif self.architecture == 'sac'  :
                agent = SAC(writer, self.device, state_dim, action_dim, self.agent_args)
            elif self.architecture == 'ddpg'  :
                from deep_learning.utils.noise import OUNoise
                noise = OUNoise(action_dim,0)
                agent = DDPG(writer, self.device, state_dim, action_dim, self.agent_args, noise)
            if self.loadExistingNetwork != 'no':
                agent.load_state_dict(torch.load("./model_weights/"+self.loadExistingNetwork))

            self.agents.append(agent)
            self.epochs.append(0)
            self.conFails.append(0)
            self.storedNetworkWeights.append([])
            self.learningLog.append([])
            #initialize and transfer weights
            learnerProxy=xmlrpc.client.ServerProxy("http://"+IP+":9000")
            if learnerProxy.initializeAgent()==False:
                print("Agent initialization of "+host+" failed!")

            else:
                state_dict_cpu = {k: v.cpu() for k, v in agent.state_dict().items()}
                model_bytes = pickle.dumps(state_dict_cpu)
                if learnerProxy.setModelWeights(xmlrpc.client.Binary(model_bytes))==True:
                    pass
                else:
                    print("Transfer of weights to "+host+" failed!")
            
        #test loop
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.learning_loop(self.robotLearningInstances, self.learning_callback))

        #saving experiment results^
        self.saveExperimentData("experimentData")

for i in range(1):
    Learner=CollectiveDeepReinforcementLearner(learningParams,modelKnowledge4)
    Learner.initializeLocalLearners()
    Learner.learning()
   
# for i in range(2):
#     Learner=CollectiveDeepReinforcementLearner(learningParams,modelKnowledge1)
#     Learner.initializeLocalLearners()
#     Learner.learning()

# for i in range(learningParams['number_of_experiments']):
#     Learner=CollectiveDeepReinforcementLearner(learningParams,modelKnowledge0)
#     Learner.initializeLocalLearners()
#     Learner.learning()
   
# for i in range(learningParams['number_of_experiments']):
#     Learner=CollectiveDeepReinforcementLearner(learningParams,modelKnowledge1)
#     Learner.initializeLocalLearners()
#     Learner.learning()

# for i in range(learningParams['number_of_experiments']):
#     Learner=CollectiveDeepReinforcementLearner(learningParams,modelKnowledge2)
#     Learner.initializeLocalLearners()
#     Learner.learning()

# for i in range(learningParams['number_of_experiments']):
#     Learner=CollectiveDeepReinforcementLearner(learningParams,modelKnowledge3)
#     Learner.initializeLocalLearners()
#     Learner.learning()
