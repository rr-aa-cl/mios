from mios_examples import *
from industrial_tasks import *
import math
#was brauche ich?
#Move
#MoveToContact
#Grasp
#Screw
#Insert

poses={
    "idlePoseKrones",
    "standardPoseObjects",
    "screwPeg1Pose",
    "screwPeg1PoseApproach",
    "screwPeg2Pose",
    "screwPeg2PoseApproach",
    "ringPose",
    "ringPoseApproach",
    "screwPose",
    "screwPoseApproach",
    "pegPose1",
    "pegPoseApproach1",
    "pegPose2",
    "pegPose2Approach2"
}






robot_ip= "10.157.174.197"
#todo ->teach


#move(robot_ip,location)

def teach_robot_poses(robot:str,pose_name:str,port=12000):
    status=None
    index=0
    while(status!='x'):
        name=pose_name+"_"+str(index)
        print("\nteaching ",name, "for ", robot,"\n")
        index+=1
        status=input("Press key")
        call_method(robot, port, "teach_object",{"object":name})




#teach_robot_poses(robot_ip,"pose1")

start_task_and_wait(robot_ip, "MoveToCartPose",port=12000, parameters={"parameters": {"pose":"pose1_0"}})

start_task_and_wait(robot_ip,)


# for i in range(3):
#     start_task_and_wait(robot_ip, "MoveToJointPose",port=12000, parameters={"parameters": {"pose":"pose1_0"}})
#     start_task_and_wait(robot_ip, "MoveToJointPose",port=12000, parameters={"parameters": {"pose":"pose1_1"}})
#     start_task_and_wait(robot_ip, "MoveToJointPose",port=12000, parameters={"parameters": {"pose":"pose1_2"}})

#start_task_and_wait(robot_ip, "MoveToJointPose", parameters={"parameters": {"q_g": [0,0,0,0,0,0,0], "pose":"NoneObject"}})

#def move(robot, location, offset = [0,0,0], port=12000, wait = True,f_ext = [10,5], add_nullspace=False):
