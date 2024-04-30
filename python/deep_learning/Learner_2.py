import copy
import csv
import os
import time
from argparse import Action, ArgumentParser
from configparser import ConfigParser
from http.client import responses
from pickle import GLOBAL

import actionlib
import dynamic_reconfigure.client
import numpy as np
import roslib
import rospy
import torch
from agents.ddpg import DDPG
from agents.ppo import PPO
from agents.sac import SAC
from control_msgs.msg import *
from controller_manager_msgs.srv import (LoadController, SwitchController,
                                         UnloadController)
from franka_controllers.msg import JointData
from franka_example_controllers.msg import *
from franka_example_controllers.msg import JointTorqueComparison
from franka_gripper.msg import *
from franka_msgs.msg import *
from geometry_msgs.msg import Pose, PoseStamped, Wrench, WrenchStamped
from pyJoules.energy_meter import measure_energy
from scipy.spatial.transform import Rotation as R_
from utils.utils import Dict, RunningMeanStd, make_transition

from interpolator import cartesianInterpolator, interpolator

os.makedirs('./model_weights', exist_ok=True)



my_franka_state=None

parser = ArgumentParser('parameters')

parser.add_argument("--algo", type=str, default = 'ddpg', help = 'algorithm to adjust (default : ppo)')
parser.add_argument('--train', type=bool, default=True, help="(default: True)")
parser.add_argument('--epochs', type=int, default=502, help='number of epochs, (default: 1000)')
parser.add_argument('--tensorboard', type=bool, default=False, help='use_tensorboard, (default: False)')
parser.add_argument("--load", type=str, default = 'no', help = 'load network name in ./model_weights')
parser.add_argument("--save_interval", type=int, default = 100, help = 'save interval(default: 100)') 
parser.add_argument("--print_interval", type=int, default = 1, help = 'print interval(default : 20)')
parser.add_argument("--reward_scaling", type=float, default = 1, help = 'reward scaling(default : 1)')
args = parser.parse_args()
parser = ConfigParser()
parser.read('config.ini')
agent_args = Dict(parser,args.algo)

AllInfo=[]


#todo transfer, safety, autonomy


class DeepReinforcementLearner():
    def __init__(self):
        self.experiment_ID=0
        self.numberOfExperiments=5
        self.TaskNumber=-1

        self.end2end=False
        self.penaltyMultiplier=0.0001
        self.generalize=False


        #self.pegsToLearn=[10,20,30,40,50,60]

        #need to teach 10 and 50!

        #change learner noise!

        self.pegsToLearn=[40]

        self.successDistances=[0.005,0.005,0.005,0.005,0.005,0.005]
        self.offsetDistances=[0.04,0.04,0.04,0.04,0.04,0.04]
        self.actionScaling=[2.5,2.5,10,1,1,0.5]

        self.graspingOffsets=[0,0,0.005,0,0,0]

        self.transferNets=[]
        #self.transferNets.append('agent_6_0_500')
        #self.transferNets.append('agent_4_0_500')
        #self.transferNets.append('agent_3_0_500')


        self.goalPoses=[]
        self.jointWaitPoses=[]
        self.jointGraspPoses=[]
        #testen
        self.initJointPose=[0.0810330426411173, -0.0436181995218356, -0.1789921691853954, -2.5373878185691585, -0.01757423325876395, 2.462344768285751, -0.8510199553999636]

        goalPose1=[0]
        goalPose2=[0.0120725034321892, 0.9995460526623938, -0.02725234245189355, 0.0, 0.9996412640298592, -0.012705269480187412, -0.023166058737497455, 0.0, -0.023502243412642627, -0.026963412862018327, -0.9993601047277229, 0.0, 0.45211300449064024, -0.14620654520138968, 0.08541690041783948, 1.0]
        goalPose3=[0.0476105546666527, 0.9985898068686526, -0.023073352672915826, 0.0, 0.9988340525013778, -0.047751088638087386, -0.005578171632398879, 0.0, -0.006672211502486881, -0.022781309120432813, -0.9997182070705851, 0.0, 0.45233391955046026, -0.10180736418185884, 0.0876004580505516, 1.0]
        goalPose4=[0.02692702734274181, 0.9986272359849964, -0.04471381943714888, 0.0, 0.9996269202942671, -0.026958435337542608, -9.944022590327786e-05, 0.0, -0.0013047434482848636, -0.04469532051229058, -0.9989998127971984, 0.0, 0.4525996062450062, -0.047418731207636525, 0.0871263420455722, 1.0]
        goalPose5=[0]
        goalPose6=[0.023742306444914076, 0.9990723570535277, -0.035657750313118214, 0.0, 0.9996982452979111, -0.023888370335727976, -0.003675732877887737, 0.0, -0.004524215760202191, -0.035560404690883445, -0.9993572880056341, 0.0, 0.4541435494158818, 0.09149782010620235, 0.08653875335239891, 1.0]
        jointWaitPose1=[0]
        jointWaitPose2=[-0.03316290285189946, 0.13537220420599363, -0.2767637523044263, -2.472397739544249, 0.08594874480791624, 2.591243781893972, -1.1287527839132947]
        jointWaitPose3=[-0.007624855961127126, 0.02067288103150694, -0.2114306067280602, -2.5502978994469894, 0.055859484853872855, 2.5905562474727626, -1.0171133558532937]
        jointWaitPose4=[0.008403359189335857, 0.004084472279766933, -0.10175878094581135, -2.5462618208714733, -0.06127102342247867, 2.56680330379804, -0.8141771556834388]
        jointWaitPose5=[0]
        jointWaitPose6=[0.11434576136292071, 0.06756078356399871, 0.07851243793036775, -2.509169019137629, -0.05824720707535744, 2.570069473028183, -0.5150685675177309]

        jointGraspPose1=[0.29,0.1,0.172,-2.39,-0.207,2.764,-0.15]
        jointGraspPose2=[0.281,0.1,0.1398,-2.455,-0.169,2.65,-0.2267]
        jointGraspPose3=[0.22086,0.1,0.1,-2.5126,-0.086,2.821,-0.405]
        jointGraspPose4=[0.16,0.1,0.053,-2.554,-0.108,2.8373,-0.4645]
        jointGraspPose5=[0.111, 0.1, -0.030, -2.614, -0.03, 2.72,-0.679]
        jointGraspPose6=[0.036, 0.09, -0.121, -2.59, 0.06, 2.688,-0.933]

        self.goalPoses.append(goalPose1)
        self.goalPoses.append(goalPose2)
        self.goalPoses.append(goalPose3)
        self.goalPoses.append(goalPose4)
        self.goalPoses.append(goalPose5)
        self.goalPoses.append(goalPose6)
        self.jointWaitPoses.append(jointWaitPose1)
        self.jointWaitPoses.append(jointWaitPose2)
        self.jointWaitPoses.append(jointWaitPose3)
        self.jointWaitPoses.append(jointWaitPose4)
        self.jointWaitPoses.append(jointWaitPose5)
        self.jointWaitPoses.append(jointWaitPose6)
        self.jointGraspPoses.append(jointGraspPose1)
        self.jointGraspPoses.append(jointGraspPose2)
        self.jointGraspPoses.append(jointGraspPose3)
        self.jointGraspPoses.append(jointGraspPose4)
        self.jointGraspPoses.append(jointGraspPose5)
        self.jointGraspPoses.append(jointGraspPose6)

        self.gripper_grasp_publisher=rospy.Publisher('/franka_gripper/grasp/goal',GraspActionGoal,queue_size=1)
        self.gripper_move_publisher=rospy.Publisher('/franka_gripper/move/goal',MoveActionGoal,queue_size=1)
        self.arm_publisherForce=rospy.Publisher('/cartesian_force_controller/wrench',WrenchStamped,queue_size=1)
        self.arm_publisherImpedance=rospy.Publisher('/cartesian_impedance_example_controller/equilibrium_pose',PoseStamped,queue_size=1)
        self.arm_publisherJointImpedance=rospy.Publisher('/joint_impedance_controller/joint_d_',JointData,queue_size=1)
        self.recovery_publisher=rospy.Publisher('/franka_control/error_recovery/goal',franka_msgs.msg.ErrorRecoveryActionGoal ,queue_size=1)

        rospy.init_node('learner')
        self.r = rospy.Rate(20)
        rospy.wait_for_service("controller_manager/switch_controller")
        #Load Controllers
        try: 
            self.load_controller=rospy.ServiceProxy('controller_manager/load_controller',LoadController)
            self.unload_controller=rospy.ServiceProxy('controller_manager/unload_controller',UnloadController)
            self.switch_controller=rospy.ServiceProxy('controller_manager/switch_controller',SwitchController)
            ret=self.load_controller('cartesian_force_controller')
            ret=self.load_controller('joint_impedance_controller')
            ret=self.load_controller('cartesian_impedance_example_controller')

        except rospy.ServiceException as e:
            print ("Service call failed: %s"%e)
        self.cartesianImpedanceReconfigure=dynamic_reconfigure.client.Client('cartesian_impedance_example_controller/dynamic_reconfigure_compliance_param_node',timeout=4, config_callback=None)
        self.jointImpedanceReconfigure=dynamic_reconfigure.client.Client('joint_impedance_controller/dynamic_reconfigure_joint_compliance_param_node',timeout=4, config_callback=None)

        print("Initialization successful!")

    def resetPose(self):
        
        #loop to reset to retraction pose
        resetSuccessful=False
        while(resetSuccessful==False):
            

            my_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)
            qStart=my_franka_state.q
            try: 
                ret=self.switch_controller(['joint_impedance_controller'],['cartesian_impedance_example_controller'],1, False, 2)
            except rospy.ServiceException as e:
                print ("Service call failed: %s"%e)    
            time.sleep(1)
            interp=interpolator(2,qStart,self.jointWaitPoses[self.TaskNumber-1])
            for i in range(40):
                recGoal=franka_msgs.msg.ErrorRecoveryActionGoal()
                self.recovery_publisher.publish(recGoal)
                jointpose = JointData()
                qD=interp.getInterpValue(0.05)
                jointpose.joint_data=qD
                self.arm_publisherJointImpedance.publish(jointpose)
                self.r.sleep()
            interp.reset()

            try: 
                ret=self.switch_controller(['cartesian_impedance_example_controller'],['joint_impedance_controller'],1, False, 2)
            except rospy.ServiceException as e:
                print ("Service call failed: %s"%e)

            self.setCartesianStiffness()

            my_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)
            tStart=my_franka_state.O_T_EE
            interp=cartesianInterpolator(2,tStart,self.retractPose)

            pose = geometry_msgs.msg.PoseStamped()
            for i in range(40):
                recGoal=franka_msgs.msg.ErrorRecoveryActionGoal()
                self.recovery_publisher.publish(recGoal)
                tD,qD=interp.getInterpValue(0.05)
                pose.pose.orientation.w=qD.w
                pose.pose.orientation.x=qD.x
                pose.pose.orientation.y=qD.y
                pose.pose.orientation.z=qD.z

                pose.pose.position.x=tD[12]
                pose.pose.position.y=tD[13]
                pose.pose.position.z=tD[14]
                self.arm_publisherImpedance.publish(pose)
                self.r.sleep()
            interp.reset()

            my_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)
            tPose=my_franka_state.O_T_EE

            # print(abs(tPose[12]-self.retractPose[12]))
            # print(abs(tPose[13]-self.retractPose[13]))
            # print(abs(tPose[14]-self.retractPose[14]))

            if(abs(tPose[12]-self.retractPose[12])<0.005 and abs(tPose[13]-self.retractPose[13])<0.005 and abs(tPose[14]-self.retractPose[14])<0.01):
                resetSuccessful=True


        my_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)

        tStart=my_franka_state.O_T_EE
        interp=cartesianInterpolator(2,tStart,self.initialPose)
        for i in range(40):

            tD,qD=interp.getInterpValue(0.05)
            pose.pose.orientation.w=qD.w
            pose.pose.orientation.x=qD.x
            pose.pose.orientation.y=qD.y
            pose.pose.orientation.z=qD.z


            pose.pose.position.x=tD[12]
            pose.pose.position.y=tD[13]
            pose.pose.position.z=tD[14]
            self.arm_publisherImpedance.publish(pose)
            self.r.sleep()
        interp.reset()
    
    def graspPeg(self):
        print("Grasping")
        gag=GraspActionGoal()

        gag.goal.width=0.001
        gag.goal.epsilon.inner=0.5
        gag.goal.epsilon.outer=0.5
        gag.goal.speed=0.1
        gag.goal.force=80

        self.gripper_grasp_publisher.publish(gag)
        time.sleep(1)

    def releasePeg(self):
        print("Release")
        gag=MoveActionGoal()
        gag.goal.width=0.06
        gag.goal.speed=0.1

        self.gripper_move_publisher.publish(gag)
        time.sleep(1)

    def setCartesianStiffness(self):
        self.cartesianImpedanceReconfigure.update_configuration(
            {
                'nullspace_stiffness':0.0,
                'translational_stiffness':1500.0,
                'rotational_stiffness':50
            }
        )

    def setJointStiffness(self):
        self.cartesianImpedanceReconfigure.update_configuration(
            {
                'nullspace_stiffness':0.0,
                'translational_stiffness':1500.0,
                'rotational_stiffness':50
            }
        )

    def getReward(self,new_franka_state,old_franka_state):
        dx=-abs(new_franka_state.O_T_EE[12]-self.goalPoses[self.TaskNumber-1][12])
        +abs(old_franka_state.O_T_EE[12]-self.goalPoses[self.TaskNumber-1][12])
        dy=-abs(new_franka_state.O_T_EE[13]-self.goalPoses[self.TaskNumber-1][13])+abs(old_franka_state.O_T_EE[13]-self.goalPoses[self.TaskNumber-1][13])
        dz=-(new_franka_state.O_T_EE[14]-old_franka_state.O_T_EE[14])

        #todo parameters
        reward=10*(dz+0.25*dx+0.25*dy)

        if self.end2end==False:
            penalty=(new_franka_state.O_F_ext_hat_K[0]*new_franka_state.O_F_ext_hat_K[0]+
            new_franka_state.O_F_ext_hat_K[1]*new_franka_state.O_F_ext_hat_K[1]+
            new_franka_state.O_F_ext_hat_K[3]*new_franka_state.O_F_ext_hat_K[3]+
            new_franka_state.O_F_ext_hat_K[4]*new_franka_state.O_F_ext_hat_K[4]+
            new_franka_state.O_F_ext_hat_K[5]*new_franka_state.O_F_ext_hat_K[5])
        else:
            penalty=(new_franka_state.tau_ext_hat_filtered [0]*new_franka_state.tau_ext_hat_filtered [0]+
            new_franka_state.tau_ext_hat_filtered [1]*new_franka_state.tau_ext_hat_filtered [1]+
            new_franka_state.tau_ext_hat_filtered [2]*new_franka_state.tau_ext_hat_filtered [2]+
            new_franka_state.tau_ext_hat_filtered [3]*new_franka_state.tau_ext_hat_filtered [3]+
            new_franka_state.tau_ext_hat_filtered [4]*new_franka_state.tau_ext_hat_filtered [4]+
            new_franka_state.tau_ext_hat_filtered [5]*new_franka_state.tau_ext_hat_filtered [5]+
            new_franka_state.tau_ext_hat_filtered [6]*new_franka_state.tau_ext_hat_filtered [6])
        
        penalty=self.penaltyMultiplier*penalty
        #todo thinking
        #reward=reward-penalty

        return reward

    def getOverallReward(self,new_franka_state):
        dx=-abs(new_franka_state.O_T_EE[12]-self.goalPoses[self.TaskNumber-1][12])
        dy=-abs(new_franka_state.O_T_EE[13]-self.goalPoses[self.TaskNumber-1][13])
        dz=-(new_franka_state.O_T_EE[14]-self.goalPoses[self.TaskNumber-1][14])

        #todo parameters
        reward=100*(dz+dx+dy)

        if self.end2end==False:
            penalty=(new_franka_state.O_F_ext_hat_K[0]*new_franka_state.O_F_ext_hat_K[0]+
            new_franka_state.O_F_ext_hat_K[1]*new_franka_state.O_F_ext_hat_K[1]+
            new_franka_state.O_F_ext_hat_K[3]*new_franka_state.O_F_ext_hat_K[3]+
            new_franka_state.O_F_ext_hat_K[4]*new_franka_state.O_F_ext_hat_K[4]+
            new_franka_state.O_F_ext_hat_K[5]*new_franka_state.O_F_ext_hat_K[5])
        else:
            penalty=(new_franka_state.tau_ext_hat_filtered [0]*new_franka_state.tau_ext_hat_filtered [0]+
            new_franka_state.tau_ext_hat_filtered [1]*new_franka_state.tau_ext_hat_filtered [1]+
            new_franka_state.tau_ext_hat_filtered [2]*new_franka_state.tau_ext_hat_filtered [2]+
            new_franka_state.tau_ext_hat_filtered [3]*new_franka_state.tau_ext_hat_filtered [3]+
            new_franka_state.tau_ext_hat_filtered [4]*new_franka_state.tau_ext_hat_filtered [4]+
            new_franka_state.tau_ext_hat_filtered [5]*new_franka_state.tau_ext_hat_filtered [5]+
            new_franka_state.tau_ext_hat_filtered [6]*new_franka_state.tau_ext_hat_filtered [6])
        
        penalty=self.penaltyMultiplier*penalty
        #todo thinking
        #reward=reward-penalty

        return reward

    def getEulerFromPose(self, pose):
        eulerPose=[pose[12],pose[13],pose[14],0,0,0]
        r = R_.from_matrix([[pose[0], pose[4], pose[8]],
                        [pose[1], pose[5], pose[9]],
                        [pose[2], pose[6], pose[10]]])
        angles=r.as_euler('zyx', degrees=False)

        eulerPose[3:5]=angles

        return eulerPose



    def getState(self):
        my_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)

        eulerPose=self.getEulerFromPose(my_franka_state.O_T_EE)

        if self.generalize==True:
            eulerPose[0]=eulerPose[0]-self.goalPoses[self.TaskNumber-1][12]
            eulerPose[1]=eulerPose[1]-self.goalPoses[self.TaskNumber-1][13]
            eulerPose[2]=eulerPose[2]-self.goalPoses[self.TaskNumber-1][14]

        if self.end2end==False:
            state = [eulerPose[0],eulerPose[1],eulerPose[2],
            eulerPose[3],eulerPose[4],eulerPose[5],
            my_franka_state.O_dP_EE_c[0],my_franka_state.O_dP_EE_c[1],my_franka_state.O_dP_EE_c[2],
            my_franka_state.O_dP_EE_c[3],my_franka_state.O_dP_EE_c[4],my_franka_state.O_dP_EE_c[5],
            my_franka_state.O_F_ext_hat_K[0],my_franka_state.O_F_ext_hat_K[1],my_franka_state.O_F_ext_hat_K[2],
            my_franka_state.O_F_ext_hat_K[3],my_franka_state.O_F_ext_hat_K[4],my_franka_state.O_F_ext_hat_K[5]]

        else:
            state = [my_franka_state.q[0],my_franka_state.q[1],my_franka_state.q[2],
            my_franka_state.q[3],my_franka_state.q[4],my_franka_state.q[5],
            my_franka_state.q[6],
            my_franka_state.dq[0],my_franka_state.dq[1],my_franka_state.dq[2],
            my_franka_state.dq[3],my_franka_state.dq[4],my_franka_state.dq[5],
            my_franka_state.dq[6],
            my_franka_state.tau_ext_hat_filtered[0],my_franka_state.tau_ext_hat_filtered[1],my_franka_state.tau_ext_hat_filtered[2],
            my_franka_state.tau_ext_hat_filtered[3],my_franka_state.tau_ext_hat_filtered[4],my_franka_state.tau_ext_hat_filtered[5],
            my_franka_state.tau_ext_hat_filtered[6]]
        return state

    def applyAction(self,action):
        actionWrench=action
        #Execute Action
        wrench = geometry_msgs.msg.WrenchStamped()

        wrench.wrench.force.x=actionWrench[0]*self.actionScaling[0]
        wrench.wrench.force.y=actionWrench[1]*self.actionScaling[0]
        wrench.wrench.force.z=actionWrench[2]*self.actionScaling[0]
        wrench.wrench.torque.x=actionWrench[3]*self.actionScaling[0]
        wrench.wrench.torque.y=actionWrench[4]*self.actionScaling[0]
        wrench.wrench.torque.z=actionWrench[5]*self.actionScaling[0]

        self.arm_publisherForce.publish(wrench)
        self.r.sleep()

    def saveData(self,DataList):
        #testen
        os.makedirs('./model_weights/'+ str(self.experiment_ID) +'/'+str(self.TaskNumber)+'/agents',exist_ok=True)
        torch.save(self.agent.state_dict(),'./model_weights/'+ str(self.experiment_ID) +'/'+str(self.TaskNumber)+'/agents/'+str(self.expI)+'_'+str(self.n_epi),)

        f = open('./model_weights/'+ str(self.experiment_ID) +'/'+str(self.TaskNumber)+'/'+str(self.expI), 'w')
        writer = csv.writer(f)
        for d in DataList:
            writer.writerow(d)
        f.close()

    def sampleAction(self):
        pass

    def moveToInitPose(self):
        my_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)
        qStart=my_franka_state.q
        try: 
            ret=self.switch_controller(['joint_impedance_controller'],['cartesian_impedance_example_controller'],1, False, 2)
        except rospy.ServiceException as e:
            print ("Service call failed: %s"%e)    
        interp=interpolator(3,qStart,self.initJointPose)
        for i in range(60):
            jointpose = JointData()
            qD=interp.getInterpValue(0.05)
            jointpose.joint_data=qD
            self.arm_publisherJointImpedance.publish(jointpose)
            self.r.sleep()
        interp.reset()


    def moveToPegGraspingPose(self):
        my_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)
        qStart=my_franka_state.q
        try: 
            ret=self.switch_controller(['joint_impedance_controller'],['cartesian_impedance_example_controller'],1, False, 2)
        except rospy.ServiceException as e:
            print ("Service call failed: %s"%e)    

        interp=interpolator(2,qStart,self.jointWaitPoses[self.TaskNumber-1])
        for i in range(40):
            jointpose = JointData()
            qD=interp.getInterpValue(0.05)
            jointpose.joint_data=qD
            self.arm_publisherJointImpedance.publish(jointpose)
            self.r.sleep()
        interp.reset()

        my_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)
        tStart=my_franka_state.O_T_EE
        try: 
            ret=self.switch_controller(['cartesian_impedance_example_controller'],['joint_impedance_controller'],1, False, 2)
        except rospy.ServiceException as e:
            print ("Service call failed: %s"%e)    

        tp=self.goalPoses[self.TaskNumber-1]
        tp[14]=tp[14]+self.graspingOffsets[self.TaskNumber-1]

        interp=cartesianInterpolator(2,tStart,self.goalPoses[self.TaskNumber-1])
        pose = geometry_msgs.msg.PoseStamped()
        for i in range(40):
            tD,qD=interp.getInterpValue(0.05)
            pose.pose.orientation.w=qD.w
            pose.pose.orientation.x=qD.x
            pose.pose.orientation.y=qD.y
            pose.pose.orientation.z=qD.z

            pose.pose.position.x=tD[12]
            pose.pose.position.y=tD[13]
            pose.pose.position.z=tD[14]
            self.arm_publisherImpedance.publish(pose)
            self.r.sleep()
        interp.reset()


    def learning(self):
        for peg in self.pegsToLearn:

            self.releasePeg()
            self.moveToInitPose()

            self.TaskNumber=int(peg/10)
            self.initialPose=copy.deepcopy(self.goalPoses[self.TaskNumber-1])
            self.retractPose=copy.deepcopy(self.goalPoses[self.TaskNumber-1])
            #todo - improve
            self.initialPose[14]=self.initialPose[14]+self.offsetDistances[self.TaskNumber-1]
            self.retractPose[14]=self.retractPose[14]+self.offsetDistances[self.TaskNumber-1]+0.1

            #move to joint pose and grasp
            self.moveToPegGraspingPose() 
            self.graspPeg()


            for expI in range(0,self.numberOfExperiments):
                self.expI=expI
                #init learner
                device = 'cpu'
                    
                if args.tensorboard:
                    from torch.utils.tensorboard import SummaryWriter
                    writer = SummaryWriter()
                else:
                    writer = None
                #Actions/States
                if self.end2end==False:
                    action_dim = 6
                    state_dim = 18
                else:
                    action_dim = 7
                    state_dim = 21

                state_rms = RunningMeanStd(state_dim)

                if args.algo == 'ppo' :
                    self.agent = PPO(writer, device, state_dim, action_dim, agent_args)
                elif args.algo == 'sac' :
                    self.agent = SAC(writer, device, state_dim, action_dim, agent_args)
                elif args.algo == 'ddpg' :
                    from utils.noise import OUNoise
                    noise = OUNoise(action_dim,0)
                    self.agent = DDPG(writer, device, state_dim, action_dim, agent_args, noise)
                if args.load != 'no':
                    self.agent.load_state_dict(torch.load("./model_weights/"+args.load))

                score_lst = []
                costScore_lst = []
                state_lst = []

                DataList=[]
                #todo merge!
                if agent_args.on_policy == True:
                    #needs to be added
                    pass
                            
                else : # off policy 
                    for n_epi in range(args.epochs):
                        self.n_epi=n_epi
                        score = 0.0
                        costScore=0.0
                        #testen!                        
                        self.resetPose()

                        try: 
                            ret=self.switch_controller(['cartesian_force_controller'],['cartesian_impedance_example_controller'],1, False, 2)
                        except rospy.ServiceException as e:
                            print ("Service call failed: %s"%e)

                        done = False
                        timestep=0

                        state=self.getState()
                        
                        my_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)

                        while not done:
                            timestep=timestep+1
                            #get action
                            if (args.train==True):
                                action, _ = self.agent.get_action(torch.from_numpy(np.asarray(state)).float().to(device))
                            else:
                                action, _ = self.agent.get_groundTruth(torch.from_numpy(np.asarray(state)).float().to(device))
                            action = action.cpu().detach().numpy()
                            
                            self.applyAction(action)

                            #getState
                            new_franka_state=rospy.wait_for_message('franka_state_controller/franka_states',franka_msgs.msg.FrankaState)


                            if new_franka_state.robot_mode==4:
                                recGoal=franka_msgs.msg.ErrorRecoveryActionGoal()
                                self.recovery_publisher.publish(recGoal)
                                done=True

                            reward=0
                            #reward=self.getReward(new_franka_state,my_franka_state)

                            
                            if  abs(new_franka_state.O_T_EE[12]-self.goalPoses[self.TaskNumber-1][12])<0.005 and abs(new_franka_state.O_T_EE[13]-self.goalPoses[self.TaskNumber-1][13])<0.005 and new_franka_state.O_T_EE[14]-self.goalPoses[self.TaskNumber-1][14]<self.successDistances[self.TaskNumber-1]:
                                done=True

                            if timestep>=101:
                                done=True

                            if self.initialPose[14]+0.01<new_franka_state.O_T_EE[14]:
                                done=True

                            if  abs(new_franka_state.O_T_EE[12]-self.goalPoses[self.TaskNumber-1][12])>0.03 or abs(new_franka_state.O_T_EE[13]-self.goalPoses[self.TaskNumber-1][13])>0.03 or abs(new_franka_state.O_T_EE[14]-self.goalPoses[self.TaskNumber-1][14])>0.15:
                                done=True

                            score += reward
                            if self.agent.data.data_idx > agent_args.learn_start_size: 
                                self.agent.train_net(agent_args.batch_size, n_epi)

                            next_state = self.getState()
                            if done==True:
                                reward=self.getOverallReward(new_franka_state)
                                if  abs(new_franka_state.O_T_EE[12]-self.goalPoses[self.TaskNumber-1][12])<0.005 and abs(new_franka_state.O_T_EE[13]-self.goalPoses[self.TaskNumber-1][13])<0.005 and new_franka_state.O_T_EE[14]-self.goalPoses[self.TaskNumber-1][14]<self.successDistances[self.TaskNumber-1]:
                                    reward=reward+10
                                score = reward

                            
                            transition = make_transition(state,\
                                                        action,\
                                                        np.array([reward*args.reward_scaling]),\
                                                        next_state,\
                                                        np.array([done])\
                                                        )
                            self.agent.put_data(transition) 
                            state = next_state

                            if done==True:
                                try: 
                                    ret=self.switch_controller(['cartesian_impedance_example_controller'],['cartesian_force_controller'],1, False, 2)
                                except rospy.ServiceException as e:
                                    print ("Service call failed: %s"%e)    
                                break

                        score_lst.append(score)
                        costScore_lst.append(costScore)
                        if args.tensorboard:
                            writer.add_scalar("score/score", score, n_epi)
                        if n_epi%args.print_interval==0 and n_epi!=0:
                            print("# of episode :{}, avg score : {:.3f}".format(n_epi, sum(score_lst)/len(score_lst)))

                            DataList.append([sum(score_lst)/len(score_lst),sum(costScore_lst)/len(costScore_lst)])

                            score_lst = []
                            costScore_lst=[]
                            
                        if n_epi%args.save_interval==0 and n_epi!=0:
                            self.saveData(DataList)

        try: 
            ret=self.switch_controller(['cartesian_impedance_example_controller'],['cartesian_force_controller'],1, False, 2)
        except rospy.ServiceException as e:
            print ("Service call failed: %s"%e)

        print("Finished")
        self.releasePeg()

#testen
learner=DeepReinforcementLearner()
learner.learning()

