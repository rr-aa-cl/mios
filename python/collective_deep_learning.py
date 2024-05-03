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

import asyncio
from desk.mongodb_client import MongoDBClient

modelKnowledge0={'mode':0,
                'scaling':[1,1,1,1,1,1,1],
                'actionLimits':[[-2,2],[-2,2],[-2,2],[-2,2],[-2,2],[-2,2],[-2,2]],
                'sigmaScaling':0.1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}


modelKnowledge1={'mode':1,
                'scaling':[1,1,1,1,1,1],
                'actionLimits':[[-2,2],[-2,2],[-2,2],[-2,2],[-2,2],[-2,2]],
                'sigmaScaling':0.1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}
#todo
modelKnowledge2={'mode':1,
                'scaling':[1,1,1,1,1,1],
                'actionLimits':[[-3,3],[-3,3],[-3,3],[-3,3],[-3,3],[-3,3]],
                'sigmaScaling':0.1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}
#todo
modelKnowledge3={'mode':1,
                'scaling':[1,1,1,1,1,1],
                'actionLimits':[[-3,3],[-3,3],[-3,3],[-3,3],[-3,3],[-3,3]],
                'sigmaScaling':0.1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}

learningParams= {'architecture':'sac',
                'epochs':300,
                'train':True,
                'experiment_ID': 0,
                'number_of_experiments': 5,
                'saveInterval':100,
                'frequency': 20,
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
        self.batchSizeScale=8
        self.timeoutTime=120
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print("Device: ",self.device)
        self.tags = tags

        if self.model_knowledge['mode']==0:
            self.interface='Torque'
            self.end2end=True
        else:
            self.interface='Wrench'
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
        dual_arm_system_IDs=[format(i, '03d') for i in range(0,30)]
        #dual_arm_system_IDs=[format(i, '03d') for i in range(24,25)]
        def ping_hosts(hosts):
            reachable_hosts = []
            unreachable_hosts = []
            working_IPs=[]
            for host in hosts:
                result = subprocess.run(['ping', '-c', '1', '-W', '1', "collective-"+str(host)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    working_IPs.append("collective-"+str(host))
                    reachable_hosts.append(host)
                else:
                    unreachable_hosts.append(host)
            return working_IPs, reachable_hosts, unreachable_hosts


        working_Hosts,reachable, unreachable = ping_hosts(dual_arm_system_IDs)
        print(working_Hosts)
        print("Reachable hosts:", reachable)
        print("Unreachable hosts:", unreachable)


        self.robotLearningInstances=[]
        for host in working_Hosts:
            try:
                RPC_SERVER_URL = "http://"+host+":9000"

                response = requests.get(RPC_SERVER_URL)
                response_time = response.elapsed.total_seconds()
                print("Response time:", response_time, "seconds")

                learnerProxy = xmlrpc.client.ServerProxy("http://"+host+":9000")
                print(learnerProxy)
                if(learnerProxy.running()==True):
                    IP=get_ip_address(host)
                    if(learnerProxy.setModelKnowledge(self.model_knowledge)==True and
                    learnerProxy.setLearningParams(self.learning_params)==True and
                    learnerProxy.setID(host,IP)==True):
                        self.robotLearningInstances.append([host,IP])
                    else:
                        print("Initialization of "+host+" failed!")
            except:
                print("Initialization of "+host+" failed!")

    async def rpc_call_to_learner(self,learnerProxy,index):
        task=self.loop.run_in_executor(None, getattr(learnerProxy, "learning"))
        try:
            startTime=time.time()
            await asyncio.wait_for(task,self.timeoutTime)
            print(time.time()-startTime)
            self.conFails[index]=0
        except asyncio.TimeoutError:
            print(learnerProxy," did not respond")
            self.conFails[index]+=1
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
        #Do i need to change the format?
        #print(self.agents[learner_index].data.data_idx)
        if self.agents[learner_index].data.data_idx > 512: #self.agent_args.learn_start_size: 
            startTime=time.time()
            for i in range(math.ceil(self.learning_params['maxTime']*self.learning_params['frequency']/self.batchSizeScale)):
                self.agents[learner_index].train_net(self.agent_args.batch_size*self.batchSizeScale, self.epochs[learner_index])
            print("Training time: ",time.time()-startTime)
        #4. update weights
        state_dict_cpu = {k: v.cpu() for k, v in self.agents[learner_index].state_dict().items()}
        model_bytes = pickle.dumps(state_dict_cpu)
        if learnerProxy.setModelWeights(xmlrpc.client.Binary(model_bytes))==True:
            pass
        else:
            print("Transfer of weights to "+host+" failed!")   

        #5. Store weights if needed
        if self.epochs[learner_index]%self.saveInterval==0:
            self.storedNetworkWeights[learner_index].append(copy.deepcopy(self.agents[learner_index].state_dict()))     
        #6. increment respective  epoch
        self.epochs[learner_index]+=1
        #7. start new learning epoch again
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
        for i in range(len(self.robotLearningInstances)):
            host,IP=self.robotLearningInstances[i]
            os.makedirs(path+"/"+folder_name+"/"+str(i)+"/network_weights/"+host)   
            for j in range(len(self.storedNetworkWeights[i])):         
                torch.save(self.agents[i].state_dict(),path+"/"+folder_name+"/"+str(i)+"/network_weights/"+host+"/"+str((j+1)*self.saveInterval))
               # mongo_data["n"+str(j+1)]["weights"] = self.storedNetworkWeights[i]

        #save experiment parameters                
        experiments_params = {'learning_params': self.learning_params, 'model_knowledge': self.model_knowledge}
        with open(path+"/"+folder_name+"/"+str(i)+'/experiments_params.pkl', 'wb') as f:
            pickle.dump(experiments_params, f)

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

for i in range(learningParams['number_of_experiments']):
    Learner=CollectiveDeepReinforcementLearner(learningParams,modelKnowledge1)
    Learner.initializeLocalLearners()
    Learner.learning()
   
