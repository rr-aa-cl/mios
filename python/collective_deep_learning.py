import subprocess
from deep_learning.agents.ppo import PPO
from deep_learning.agents.sac import SAC
from deep_learning.agents.ddpg import DDPG
from deep_learning.utils.utils import Dict
from configparser import ConfigParser
from torch.utils.tensorboard import SummaryWriter
import requests
import xmlrpc.client
import pickle
import socket
import numpy as np
import torch

import asyncio

modelKnowledge={'mode':1,
                'scaling':[1,1,1,1,1,1],
                'actionLimits':[[-3,3],[-3,3],[-3,3],[-3,3],[-3,3],[-3,3]],
                'sigmaScaling':0.1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}

learningParams= {'architecture':'sac',
                'epochs':500,
                'train':True,
                'experiment_ID': 0,
                'number_of_experiments': 5,
                'frequency': 20,
                'taskID':0,
                'logging':True,
                'maxTime':5,
                'load':'no'}


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
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if modelKnowledge['mode']==0:
            self.interface='Torque'
            self.end2end=True
        else:
            self.interface='Wrench'
            self.end2end=False

        parser = ConfigParser()
        parser.read('deep_learning/config.ini')
        self.agent_args = Dict(parser,self.architecture)

    def initializeLocalLearners(self):
        dual_arm_system_IDs=[format(i, '03d') for i in range(1, 30)]
        dual_arm_system_IDs=[format(i, '03d') for i in range(24, 26)]
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

    async def rpc_call_to_learner(self,learnerProxy,index):
        await self.loop.run_in_executor(None, getattr(learnerProxy, "learning"))
        return index

    async def learning_loop(self,learningInstances,callback):
        self.learningTasks=set()
        index=0
        for host,IP in learningInstances:
            learnerProxy = xmlrpc.client.ServerProxy("http://"+host+":9000")
            call_task = asyncio.create_task(self.rpc_call_to_learner(learnerProxy,index))
            self.learningTasks.add(call_task)
            index+=1

        while len(self.learningTasks)>0:
            print("learningTasks")
            done, pending=await asyncio.wait(self.learningTasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                index=task.result()
                isFinished=callback(index)
                if isFinished==False:
                    host,IP=self.robotLearningInstances[index]
                    learnerProxy=xmlrpc.client.ServerProxy("http://"+IP+":9000")
                    call_task = asyncio.create_task(self.rpc_call_to_learner(learnerProxy,index))
                    self.learningTasks.add(call_task)
            self.learningTasks-=done
    
    def learning_callback(self,learner_index):
        host,IP=self.robotLearningInstances[learner_index]
        learnerProxy=xmlrpc.client.ServerProxy("http://"+IP+":9000")
        #1. get new trial data
        new_transitions=learnerProxy.getNewExperimentData()
        #2. append data to agent
        for transition in new_transitions:
            self.agents[learner_index].put_data(transition) 
        #3. train model -> improve!
        #Do i need to change the format?
        #print(self.agents[learner_index].data.data_idx)
        if self.agents[learner_index].data.data_idx > self.agent_args.learn_start_size: 
            print("TRAINING")
            for i in range(int(self.learning_params['maxTime']*self.learning_params['frequency'])):
                self.agents[learner_index].train_net(self.agent_args.batch_size, self.epochs[learner_index])
        #4. update weights
        model_bytes = pickle.dumps(self.agents[learner_index].state_dict())
        if learnerProxy.setModelWeights(xmlrpc.client.Binary(model_bytes))==True:
            pass
        else:
            print("Transfer of weights to "+host+" failed!")        
        #5. increment respective  epoch
        self.epochs[learner_index]+=1
        #6. start new learning epoch again
        if self.epochs[learner_index]<self.learning_params['epochs']:
            return False
        else:
            return True


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
        self.epochs=[]
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
            #initialize and transfer weights
            learnerProxy=xmlrpc.client.ServerProxy("http://"+IP+":9000")
            if learnerProxy.initializeAgent()==False:
                print("Agent initialization of "+host+" failed!")

            else:
                model_bytes = pickle.dumps(agent.state_dict())

                if learnerProxy.setModelWeights(xmlrpc.client.Binary(model_bytes))==True:
                    pass
                else:
                    print("Transfer of weights to "+host+" failed!")
            
        #test loop
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.learning_loop(self.robotLearningInstances, self.learning_callback))



Learner=CollectiveDeepReinforcementLearner(learningParams,modelKnowledge)
Learner.initializeLocalLearners()
Learner.learning()


    
