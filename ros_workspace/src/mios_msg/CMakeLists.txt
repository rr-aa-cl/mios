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
)

generate_messages()

catkin_package(CATKIN_DEPENDS message_runtime)

include_directories(
)

