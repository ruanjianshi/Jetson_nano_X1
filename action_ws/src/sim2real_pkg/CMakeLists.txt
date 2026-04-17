cmake_minimum_required(VERSION 3.0.2)
project(sim2real_pkg)

find_package(catkin REQUIRED COMPONENTS
  rospy
  actionlib
  actionlib_msgs
  std_msgs
  sensor_msgs
  cv_bridge
  message_generation
)

add_message_files(
  FILES
  DetectionResult.msg
  ModelInfo.msg
)

add_action_files(
  DIRECTORY action
  FILES
  ONNXInference.action
)

generate_messages(
  DEPENDENCIES
  std_msgs
  actionlib_msgs
  sensor_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy actionlib actionlib_msgs std_msgs sensor_msgs cv_bridge message_runtime
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

catkin_install_python(PROGRAMS
  scripts/rl_inference/rl_onnx_inference.py
  scripts/rl_inference/tensorrt_rl_inference.py
  scripts/rl_inference/rl_model_sim_test.py
  scripts/yolo_inference/onnx_inference.py
  scripts/tools/pt2onnx_converter.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

install(DIRECTORY models/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/models
)

install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
)
