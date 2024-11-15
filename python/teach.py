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

teach_robot_poses(robot_ip,13000)

