from mios_examples import *
from industrial_tasks import *
import math
#was brauche ich?
#Move
#MoveToContact
#Grasp
#Screw
#Insert

posesR1=[
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
    "pegPose2Approach2",
    "screwPeg1InsertionPose",
    "screwPeg1InsertionPoseApproach",
    "screwPeg2InsertionPose",
    "screwPeg2InsertionPoseApproach",
]

posesL1=[
]

posesL2=[
]


robot_ip= "10.157.174.197"
#todo ->teach


#move(robot_ip,location)






#teach_robot_poses(robot_ip,13000)




release(robot_ip,13000)
#result=start_task_and_wait(robot_ip, "MoveToCartPose",port=13000, parameters={"parameters": {"pose":"idlePoseKrones"}})
#result=start_task_and_wait(robot_ip, "MoveToJointPose",port=13000, parameters={"parameters": {"pose":"idlePoseKrones"}})

# if result['result']['result']==False:
#     exit
#start_task_and_wait(robot_ip, "MoveToJointPose",port=13000, parameters={"parameters": {"pose":"standardPoseObjects"}})
# start_task_and_wait(robot_ip, "MoveToCartPose",port=13000, parameters={"parameters": {"pose":"screwPeg1PoseApproach"}})
# start_task_and_wait(robot_ip, "MoveToCartPose",port=13000, parameters={"parameters": {"pose":"screwPeg1Pose"}})
# graspObject(robot_ip,"screwPeg",13000)
# start_task_and_wait(robot_ip, "MoveToCartPose",port=13000, parameters={"parameters": {"pose":"screwPeg1PoseApproach"}})

# start_task_and_wait(robot_ip, "MoveToJointPose",port=13000, parameters={"parameters": {"pose":"idlePoseKrones"}})
# start_task_and_wait(robot_ip, "MoveToCartPose",port=13000, parameters={"parameters": {"pose":"screwPeg1InsertionPoseApproach"}})
# start_task_and_wait(robot_ip, "MoveToCartPose",port=13000, parameters={"parameters": {"pose":"screwPeg1InsertionPose"}})

move(robot_ip,"idlePoseKrones",port=13000,wait=True,cartesian=True,nullspace=True,accuracy=True)
move(robot_ip,"standardPoseObjects",port=13000,wait=True,cartesian=True,nullspace=True)

# def screw(robot,approach,location,port=12000, wait=True):
# screw(robot_ip,)


# start_task_and_wait(robot_ip, "MoveToJointPose",port=13000, parameters={"parameters": {"pose":"screwPeg2InsertionPoseApproach"}})
# start_task_and_wait(robot_ip, "MoveToCartPose",port=13000, parameters={"parameters": {"pose":"screwPeg2InsertionPose"}})
#release(robot_ip,13000)
#call_method(robot_ip, 13000, "grasp", {"force":100, "speed":0.5, "width":0, "epsilon_inner":1, "epsilon_outer":1})

# for i in range(3):

#     response1=start_task(robot_ip, "MoveToCartPose",port=12000, parameters={"parameters": {"pose":"testpose",'vel':[0.1,0.1]}})
#     response2=start_task(robot_ip, "MoveToCartPose",port=13000, parameters={"parameters": {"pose":posesR1[0]}})
#     response3=start_task(robot_ip, "MoveToCartPose",port=14000, parameters={"parameters": {"pose":"testpose"}})
#     wait_for_task(robot_ip, response1["result"]["task_uuid"], 12000)
#     response=wait_for_task(robot_ip, response2["result"]["task_uuid"], 13000)
#     wait_for_task(robot_ip, response3["result"]["task_uuid"], 14000)

#     response1=start_task(robot_ip, "MoveToCartPose",port=12000, parameters={"parameters": {"pose":"testpose1"}})
#     response2=start_task(robot_ip, "MoveToCartPose",port=13000, parameters={"parameters": {"pose":posesR1[1]}})
#     response3=start_task(robot_ip, "MoveToCartPose",port=14000, parameters={"parameters": {"pose":"testpose1"}})
#     wait_for_task(robot_ip, response1["result"]["task_uuid"], 12000)
#     response=wait_for_task(robot_ip, response2["result"]["task_uuid"], 13000)
#     wait_for_task(robot_ip, response3["result"]["task_uuid"], 14000)

#screw(robot_ip,'screwPeg2InsertionPoseApproach','screwPeg2InsertionPose',port=13000 )

# for i in range(3):s
#     start_task_and_wait(robot_ip, "MoveToJointPose",port=12000, parameters={"parameters": {"pose":"pose1_0"}})
#     start_task_and_wait(robot_ip, "MoveToJointPose",port=12000, parameters={"parameters": {"pose":"pose1_1"}})
#     start_task_and_wait(robot_ip, "MoveToJointPose",port=12000, parameters={"parameters": {"pose":"pose1_2"}})

#start_task_and_wait(robot_ip, "MoveToJointPose", parameters={"parameters": {"q_g": [0,0,0,0,0,0,0], "pose":"NoneObject"}})

#def move(robot, location, offset = [0,0,0], port=12000, wait = True,f_ext = [10,5], add_nullspace=False):
