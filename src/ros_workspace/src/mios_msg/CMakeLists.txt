cmake_minimum_required(VERSION 3.0.2)
project(mios_msg)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  std_msgs
  message_generation
)

add_service_files(DIRECTORY srv
  FILES
  StartTask.srv
  StopTask.srv
  RemoveTask.srv
  WaitForTask.srv
  PostEvent.srv
  GetEvent.srv
  SetGraspedObject.srv
  GraspObject.srv
  Grasp.srv
  IsBusy.srv
  ReleaseObject.srv
  MoveGripper.srv
  HomeGripper.srv
  TeachObject.srv
  SetObject.srv
  DownloadTaskContext.srv
  DownloadSkillContext.srv
  DownloadObjectContext.srv
  GetState.srv
  GetModel.srv
  StartDeskTask.srv
  StopDeskTask.srv
  UnlockBrakes.srv
  LockBrakes.srv
  Shutdown.srv
  PackPose.srv
  SetLiveParameter.srv
  Terminate.srv
)

generate_messages()

catkin_package(CATKIN_DEPENDS message_runtime)

include_directories(
)

