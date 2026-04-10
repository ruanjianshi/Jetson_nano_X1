cmake_minimum_required(VERSION 3.0.2)
project(opencv_cuda_pkg)

find_package(catkin REQUIRED COMPONENTS
  rospy
  actionlib
  actionlib_msgs
  std_msgs
  sensor_msgs
  cv_bridge
)

add_message_files(
  FILES
  DetectionResult.msg
)

add_action_files(
  DIRECTORY action
  FILES
  OpenCVDetection.action
  ImageProcessing.action
)

generate_messages(
  DEPENDENCIES
  std_msgs
  actionlib_msgs
  sensor_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy actionlib actionlib_msgs std_msgs sensor_msgs cv_bridge
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

catkin_install_python(PROGRAMS
  scripts/opencv_detection_server.py
  scripts/opencv_detection_client.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)