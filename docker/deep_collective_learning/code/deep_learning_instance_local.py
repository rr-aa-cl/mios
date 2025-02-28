from ll_interface import *

from deep_learning.agents.ppo import PPO
from deep_learning.agents.sac import SAC
from deep_learning.agents.ddpg import DDPG

from desk.mongodb_client import MongoDBClient


import numpy as np

from deep_learning.utils.utils import Dict, make_transition,RunningMeanStd
from scipy.spatial.transform import Rotation as R_
from configparser import ConfigParser
import torch
import copy
import csv
import sys
import os

import signal
import pickle

import time

from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn

import logging
from video.video_command import VideoRecorder

tasks={'collective-001.rsi.ei.tum.de': 'B_002_IEC-C7',
 'collective-003.rsi.ei.tum.de': 'D_028',
 'collective-004.rsi.ei.tum.de': 'D_020',
 'collective-005.rsi.ei.tum.de': 'D_027',
 'collective-006.rsi.ei.tum.de': 'D_021',
 'collective-007.rsi.ei.tum.de': 'D_022',
 'collective-008.rsi.ei.tum.de': '008_left',
 'collective-033.rsi.ei.tum.de': 'D_023',
 'collective-035.rsi.ei.tum.de': 'C_007',
 'collective-043.rsi.ei.tum.de': 'B_013',
 'collective-013.rsi.ei.tum.de': 'C_011',
 'collective-014.rsi.ei.tum.de': 'B_016',
 #'collective-015.rsi.ei.tum.de': 'C_025',
 'collective-016.rsi.ei.tum.de': 'A_026_cylinder_30',
 'collective-042.rsi.ei.tum.de': 'mercedes_star',
 'collective-041.rsi.ei.tum.de': 'A_009_hexagon-3',
 'collective-021.rsi.ei.tum.de': 'B_RS-232',
 'collective-022.rsi.ei.tum.de': 'C_009',
 'collective-023.rsi.ei.tum.de': 'C_014',
 'collective-024.rsi.ei.tum.de': 'B_014_CN',
 'collective-025.rsi.ei.tum.de': 'A_025_heart',
 'collective-026.rsi.ei.tum.de': 'A_016_cross-1',
 'collective-047.rsi.ei.tum.de': 'B_010_plugF-2'}

logger = logging.getLogger("deep_interface")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

class InterfaceServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

holding_arm_skills=[]

move_context={
                "skill":{"speed":0.5,
                         "acc":1,
                         "q_g":[0,0,0,0,0,0,0],
                         "objects":{
                             "goal_pose":"hold"
                                    }
                        },
                        "control":{
                            "control_mode":3
                        },
                        "user":{
                            "env_X":[0.001,0.001,0.001,0.001,0.001,0.001],
                            "F_ext_max":[100,50]
                        }
            }

modelKnowledge={'mode':1,
                'scaling':[1,1,1,1,1,1],
                'actionLimits':[[3,-3],[3,-3],[3,-3],[3,-3],[3,-3],[3,-3]],
                'sigmaScaling':0.1,
                'graspOrientation':[1,0,0,0,1,0,0,0,1]}

learningParams= {'architecture':'sac',
                'epochs':'300',
                'train':True,
                'experiment_ID': 0,
                'number_of_experiments': 3,
                'frequency': 25,
                'taskID':0,
                'logging':True,
                'maxTime':5,
                'load':'no'}


def get_poses(module:str):
    client=MongoDBClient("collective-"+module+".rsi.ei.tum.de")
    object=tasks["collective-"+module+".rsi.ei.tum.de"]
    logger.debug(str(object))
    object = object+"_table"
    container=client.read("miosL","environment",
                          {"name":object+"_container"})
    approach=client.read("miosL","environment",{"name":object+"_container_approach"})

    if container:
        container_cart=container[0]["O_T_OB"]
        container_q=container[0]["q"]
    if approach:
        approach_cart=approach[0]["O_T_OB"]
        approach_q=approach[0]["q"]

    container={"EE":container_cart,"q":container_q}
    approach={"EE":approach_cart,"q":approach_q}

    return approach,container

class DeepReinforcementLearner():
    def __init__(self,learning_params,model_knowledge):
        self.experiment_ID=learning_params['experiment_ID']
        self.numberOfExperiments=learning_params['number_of_experiments']
        self.TaskNumber=-1
        self.logging=learning_params['logging']
        self.architecture=learning_params['architecture']
        self.learning_params=learning_params
        self.loadExistingNetwork=learning_params['load']
        self.collective_port=9999
        self.maxTime=learning_params['maxTime']
        self.deltaTime=1/learning_params['frequency']

        self.rpc_server=InterfaceServer(("0.0.0.0", 9000), allow_none=True)


        if modelKnowledge['mode']==0:
            self.interface='Torque'
            self.end2end=True
        elif modelKnowledge['mode']==1:
            self.interface='Wrench'
            self.end2end=False
            #todo
        elif modelKnowledge['mode']==2:
            self.interface='JointPose'
            self.end2end=False
        elif modelKnowledge['mode']==3:
            self.interface='Twist'
            self.end2end=False
            
        self.penaltyMultiplier=0.0001
        self.deltaTaskLimits=[0.1,0.1,0.1,0.25,0.25,0.25]

        parser = ConfigParser()
        parser.read('deep_learning/config.ini')

        self.agent_args = Dict(parser,self.architecture)
        self.robot_ip="localhost"
        self.own_ip="localhost"
        
        self.video_flag = False

        logger.debug("initialized")


    def start_rpc_server(self):
        logger.debug("DeepLearningInstance: Starting RPC server on port 9000")
        self.rpc_server.register_introspection_functions()
        self.rpc_server.register_function(self.running, "running")
        self.rpc_server.register_function(self.setID, "setID")
        self.rpc_server.register_function(self.learning, "learning")
        self.rpc_server.register_function(self.sendTrialResult, "getTrialResult")        
        self.rpc_server.register_function(self.setModelWeights, "setModelWeights")
        self.rpc_server.register_function(self.setModelKnowledge, "setModelKnowledge")
        self.rpc_server.register_function(self.setLearningParams, "setLearningParams")
        self.rpc_server.register_function(self.initializeAgent, "initializeAgent")
        self.rpc_server.register_function(self.sendNewExperimentDataToCollective, "getNewExperimentData")
        self.rpc_server.register_function(self.start_recording, "start_recording")
        self.rpc_server.register_function(self.stop_recording, "stop_recording")
        logger.debug("RPC server is serving..")
        self.rpc_server.serve_forever()

    def stop_rpc_server(self):
        logger.debug("stop_rpc_server()")
        self.rpc_server.shutdown()
        logger.debug("Interface::stop_rpc_server.end")


    def getReward(self,new_pose,old_pose):
        d_old=0
        d_new=0        
        for i in range (3):
            d_old+=abs(self.goalPose[i]-old_pose[i])*abs(self.goalPose[i]-old_pose[i])
            d_new+=abs(self.goalPose[i]-new_pose[i])*abs(self.goalPose[i]-new_pose[i])
        
        d_old=np.sqrt(d_old)
        d_new=np.sqrt(d_new)

        reward=100*(d_old-d_new)
        
        return reward

    def running(self):
        return True
    
    def setID(self,host,IP):
        try:
            logger.debug("Setting host and ip...")
            self.robotID=host[-3:]
            self.robot_hostname=host
            self.robot_ip=IP
            self.own_ip=IP
            logger.debug("1")

            self.approachPoses,self.goalPoses=get_poses(self.robotID)
            logger.debug("2")
            self.goalPose=self.getEulerFromPose(self.goalPoses["EE"])  
            logger.debug("3")  
            self.taskFrame=np.reshape(self.goalPoses["EE"], (4, 4), order='F')[:3, :3]
            logger.debug("4")

      
            self.q_init=self.approachPoses["q"]
            logger.debug(str(self.q_init))
            logger.debug(str(self.goalPose))
            self.sender=LLSender(self.robot_ip,self.robot_ip,self.interface,self.q_init)
            logger.debug("Done")
            return True
        except:
            logger.debug("Failed")
            return False

    def getEulerFromPose(self, pose):
        eulerPose=[pose[12],pose[13],pose[14],0,0,0]
        # r = R_.from_matrix([[pose[0], pose[4], pose[8]],
        #                 [pose[1], pose[5], pose[9]],
        #                 [pose[2], pose[6], pose[10]]])
        # angles=r.as_euler('zyx', degrees=False)
        # eulerPose[3:6]=angles

        return eulerPose

    def saveData(self,DataList):
        os.makedirs('./model_weights/'+ str(self.experiment_ID) +'/'+str(self.TaskNumber)+'/agents',exist_ok=True)
        torch.save(self.agent.state_dict(),'./model_weights/'+ str(self.experiment_ID) +'/'+str(self.TaskNumber)+'/agents/'+str(self.expI)+'_'+str(self.n_epi),)

        f = open('./model_weights/'+ str(self.experiment_ID) +'/'+str(self.TaskNumber)+'/'+str(self.expI), 'w')
        writer = csv.writer(f)
        for d in DataList:
            writer.writerow(d)
        f.close()

    def sendNewExperimentDataToCollective(self):
        logger.debug("Sending trial data")
        return self.DataList
    
    def sendTrialResult(self):
        logger.debug("sending trial result")
        distance=abs(self.actualPose[0]-self.goalPose[0])**2+abs(self.actualPose[1]-self.goalPose[1])**2+abs(self.actualPose[2]-self.goalPose[2])**2

        trialResult=[self.isSuccessful,self.timestep*self.deltaTime,distance]
        return trialResult

    def setModelWeights(self,state_dict_bytes): 
        try:
            logger.debug("updating model weights...")
            state_dict = pickle.loads(state_dict_bytes.data)
            self.agent.load_state_dict(state_dict)
            logger.debug("Done")
        except:
            logger.debug("Failed")
            return False
        return True

    def setModelKnowledge(self,modelKnowledge):
        try:
            logger.debug("Setting model knowledge...")
            self.actionScaling=modelKnowledge['scaling']
            self.actionLimits=modelKnowledge['actionLimits']
            self.actionSamplingVariance=modelKnowledge['sigmaScaling']
            if modelKnowledge['mode']==0:
                self.interface='Torque'
                self.end2end=True
            elif modelKnowledge['mode']==1:
                self.interface='Wrench'
                self.graspOrientation=np.reshape(modelKnowledge['graspOrientation'], (3, 3), order='F')
                self.end2end=False
            elif modelKnowledge['mode']==2:
                self.interface='JointPose'
                self.end2end=True
            elif modelKnowledge['mode']==3:
                self.interface='Twist'
                self.graspOrientation=np.reshape(modelKnowledge['graspOrientation'], (3, 3), order='F')
                self.end2end=False
            logger.debug("Done")
        except:
            logger.debug("Failed")
            return False
        
        return True

    def setLearningParams(self,learning_params):
        try:
            logger.debug("Setting learning parameters...")
            self.experiment_ID=learning_params['experiment_ID']
            self.numberOfExperiments=learning_params['number_of_experiments']
            self.logging=learning_params['logging']
            self.architecture=learning_params['architecture']
            self.learning_params=learning_params
            self.loadExistingNetwork=learning_params['load']
            self.maxTime=learning_params['maxTime']
            self.deltaTime=1/learning_params['frequency']
            logger.debug("Done")
        except:
            logger.debug("Failed")
            return False
        return True

    def getState(self):
        robotState = False
        while not robotState:
            robotState=udp_receiver(self.own_ip,8887)


        eulerPose=self.getEulerFromPose(robotState["T_T_EE"])
        if self.end2end==False:
            state = [eulerPose[0],eulerPose[1],eulerPose[2],
            eulerPose[3],eulerPose[4],eulerPose[5],
            robotState["F_dX_EE"][0],robotState["F_dX_EE"][1],robotState["F_dX_EE"][2],
            robotState["F_dX_EE"][3],robotState["F_dX_EE"][4],robotState["F_dX_EE"][5],
            robotState["TF_F_ext_K"][0],robotState["TF_F_ext_K"][1],robotState["TF_F_ext_K"][2],
            robotState["TF_F_ext_K"][3],robotState["TF_F_ext_K"][4],robotState["TF_F_ext_K"][5]]

        else:
            state = [robotState["q"][0],robotState["q"][1],robotState["q"][2],
            robotState["q"][3],robotState["q"][4],robotState["q"][5],
            robotState["q"][6],
            robotState["dq"][0],robotState["dq"][1],robotState["dq"][2],
            robotState["dq"][3],robotState["dq"][4],robotState["dq"][5],
            robotState["dq"][6],
            robotState["tau_ext"][0],robotState["tau_ext"][1],robotState["tau_ext"][2],
            robotState["tau_ext"][3],robotState["tau_ext"][4],robotState["tau_ext"][5],
            robotState["tau_ext"][6]]
        return state,eulerPose

    def  check_status(self):
        #check if trial has violated limits
        for i in range(3):
            if(abs(self.actualPose[i]-self.goalPose[i])>self.deltaTaskLimits[i] and 
               abs(self.actualPose[i]-self.initialPose[i])>self.deltaTaskLimits[i]):
                return True
        
        if self.timestep*self.deltaTime>=self.maxTime:
            return True

        return False
    
    def check_success(self):
        success=False
        if(abs(self.actualPose[0]-self.goalPose[0])<0.003 and 
           abs(self.actualPose[1]-self.goalPose[1])<0.003 and
           abs(self.actualPose[2]-self.goalPose[2])<0.002):
            success=True
            self.isSuccessful=True

        return success

    def initializeAgent(self):
        try:
            logger.debug("Initializing Agent...")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            writer = None
            #Actions/States
            if self.end2end==False:
                action_dim = 6
                state_dim = 18
            else:
                action_dim = 7
                state_dim = 21

            self.state_rms = RunningMeanStd(state_dim)

            if self.architecture == 'ppo' :
                self.agent = PPO(writer, self.device, state_dim, action_dim, self.agent_args)
            elif self.architecture == 'sac'  :
                self.agent = SAC(writer, self.device, state_dim, action_dim, self.agent_args)
            elif self.architecture == 'ddpg'  :
                from deep_learning.utils.noise import OUNoise
                noise = OUNoise(action_dim,0)
                self.agent = DDPG(writer, self.device, state_dim, action_dim, self.agent_args, noise)

            logger.debug("Done")
        except:
            logger.debug("Failed")
            return False
        return True

    def convert_np_float64(self,obj):
        if isinstance(obj, np.float64):
            return float(obj)
        elif isinstance(obj, (list, tuple)):
            return [self.convert_np_float64(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self.convert_np_float64(value) for key, value in obj.items()}
        else:
            return obj

    def processAction(self,action):
        processedAction=copy.deepcopy(action)
        if self.interface=='Wrench' or self.interface=='Twist':
            for i in range(6):                
                processedAction[i]*=self.actionScaling[i]
                processedAction[i]= max(self.actionLimits[i][0], min(processedAction[i], self.actionLimits[i][1]))

            processedAction[0:3] = np.dot(self.graspOrientation, processedAction[0:3])
            processedAction[3:6] = np.dot(self.graspOrientation, processedAction[3:6])

            processedAction[0:3] = np.dot(self.taskFrame, processedAction[0:3])
            processedAction[3:6] = np.dot(self.taskFrame, processedAction[3:6])

        
        else:
            for i in range(7):                
                processedAction[i]*=self.actionScaling[i]
                processedAction[i]= max(self.actionLimits[i][0], min(processedAction[i], self.actionLimits[i][1]))

        return processedAction

    def learning(self, tag=" ", trial=0):
        desired_states=["q","dq","tau_ext","T_T_EE","TF_dX_EE","TF_F_ext_K"]

        #subscribe to state
        call_method(self.robot_ip,12000, "subscribe_telemetry",{"subscribe":desired_states,"ip":self.own_ip,"port":8887})
        self.DataList=[]
        self.state_lst=[]

        self.isSuccessful=False
        self.score=[]

        call_method(self.robot_ip,12000,"stop_task")   
        object=tasks["collective-"+str(self.robotID)+".rsi.ei.tum.de"]
        logger.debug(str(object))
        extract_and_reset(self.robot_ip, object) 
        # record
        # self.start_recording(tag+"_n"+str(trial))  
        self.sender.start()
        done = False
        self.timestep=0
        robot_state,self.initialPose=self.getState()
        desired_robot_pose=copy.deepcopy(robot_state[0:7])
        self.actualPose=copy.deepcopy(self.initialPose)
        logger.debug("starting")
        startingTime=time.time()
        if self.agent_args.on_policy == True:
            robot_state_=copy.deepcopy(robot_state)
            robot_state = np.clip((robot_state_ - self.state_rms.mean) / (self.state_rms.var ** 0.5 + 1e-8), -5, 5)
            while not done:
                self.state_lst.append(robot_state)
                mu,sigma = self.agent.get_action(torch.from_numpy(robot_state).float().to(self.device),scale=self.actionSamplingVariance)
                dist = torch.distributions.Normal(mu,sigma[0])
                action = dist.sample()
                log_prob = dist.log_prob(action).sum(-1,keepdim = True)
                action=self.processAction(action)
                if self.interface=="JointPose":
                    desired_robot_pose+=action
                    action=desired_robot_pose

                self.sender.send(action.tolist()) 
                time.sleep(self.deltaTime)

                try:
                    if call_method(self.robot_ip,12000, "get_state")["result"]["current_task"]=="IdleTask":
                        done=True
                except:
                    done=True

                self.lastPose=copy.deepcopy(self.actualPose)
                #startTime=time.time()
                next_robot_state_,self.actualPose=self.getState()
                #print(time.time()-startTime)
                reward=self.getReward(self.actualPose,self.lastPose)

                if(self.check_status()):
                    logger.debug("Boundaries")
                    done=True

                if(self.check_success()):
                    logger.debug("Success")
                    done=True
                

                next_robot_state = np.clip((next_robot_state_ - self.state_rms.mean) / (self.state_rms.var ** 0.5 + 1e-8), -5, 5)
                #todo
                transition = make_transition(robot_state,\
                                            action.tolist(),\
                                            reward,\
                                            next_robot_state,\
                                            done,\
                                            log_prob.detach().cpu().numpy()\
                )

                self.DataList.append(self.convert_np_float64(transition))

                if done==True:
                    if self.interface!="JointPose":
                        mu,sigma = self.agent.get_action(torch.from_numpy(robot_state).float().to(self.device),scale=self.actionSamplingVariance)
                        dist = torch.distributions.Normal(mu,sigma[0])
                        action = dist.sample()
                        action*=0
                        self.sender.send(action.tolist()) 
                        time.sleep(self.deltaTime)
                    self.sender.stop()
                    self.state_rms.update(np.vstack(self.state_lst))
                    break
                else:
                    robot_state = next_robot_state
                    robot_state_ = next_robot_state_
            
        else :  
            while not done:
                self.timestep=self.timestep+1
                if (self.learning_params["train"]==True):
                    action, _ = self.agent.get_action(torch.from_numpy(np.asarray(robot_state)).float().to(self.device),scale=self.actionSamplingVariance)
                else:
                    action, _ = self.agent.get_groundTruth(torch.from_numpy(np.asarray(robot_state)).float().to(self.device))

                #logger.debug(str(action))

                action = action.cpu().detach().numpy()
                action=action[0]
                #logger.debug(str(action))

                action=self.processAction(action)
                #logger.debug(str(action))

                if self.interface=="JointPose":
                    desired_robot_pose+=action
                    #logger.debug(desired_robot_pose)
                    action=desired_robot_pose



                self.sender.send(action.tolist()) 
                time.sleep(self.deltaTime)
                try:
                    if call_method(self.robot_ip,12000, "get_state")["result"]["current_task"]=="IdleTask":
                        logger.debug("Idle")
                        done=True
                except:
                    logger.debug("Except")
                    done=True
                self.lastPose=copy.deepcopy(self.actualPose)
                next_robot_state,self.actualPose=self.getState()
                reward=self.getReward(self.actualPose,self.lastPose)
                if(self.check_status()):
                    logger.debug("Boundaries")
                    done=True
                if(self.check_success()):
                    logger.debug("Success")
                    done=True
                transition = make_transition(robot_state,\
                                            action.tolist(),\
                                            reward,\
                                            next_robot_state,\
                                            done\
                                            )           
                self.DataList.append(self.convert_np_float64(transition))
                robot_state = next_robot_state

                if done==True:
                    if self.interface!="JointPose":
                        action, _ = self.agent.get_action(torch.from_numpy(np.asarray(robot_state)).float().to(self.device),scale=self.actionSamplingVariance)
                        action = action.cpu().detach().numpy()
                        action=action[0]
                        action*=0
                        self.sender.send(action.tolist()) 
                        time.sleep(self.deltaTime)
                    self.sender.stop()
                    break
        logger.debug("TrialTime:"+str(time.time()-startingTime))
        logger.debug("finished")

        call_method(self.robot_ip,12000, "unsubscribe_telemetry",{"subscribe":desired_states,"ip":self.own_ip,"port":8887})    
        self.stop_recording()
        self.sender.stop()
        return "finished"

    def start_recording(self, tag = "xx"):
        
        if self.video_flag:
            logger.debug("warning: recording already started")
        else:            
            try:
                self.recorder = VideoRecorder(tag)
                self.recorder.start_recording()
                logger.debug("recording starts")
                self.video_flag = True
            except:
                logger.debug("pls check the camera device")

        
    def stop_recording(self):
        if self.video_flag:
            self.recorder.stop_recording()
            logger.debug("recording ends")
            logger.debug(self.recorder.name)
            self.video_flag = False
            del self.recorder
        else:
            logger.debug("pls check if recording has been started")

if __name__ == "__main__":
        logger.debug("Version: 1.0")
        server = DeepReinforcementLearner(learningParams,modelKnowledge)
        server.start_rpc_server()
        def signal_handler(sig, frame):
            logger.debug("Shutting down the server.")
            server.rpc_server.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.pause()





