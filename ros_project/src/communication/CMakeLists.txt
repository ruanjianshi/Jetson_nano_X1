cmake_minimum_required(VERSION 3.0.2)
project(communication)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  message_generation
)

find_package(Boost REQUIRED COMPONENTS system thread)

add_service_files(FILES SerialCommunication.srv NetworkCommunication.srv)
generate_messages(DEPENDENCIES std_msgs)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs sensor_msgs message_runtime
  INCLUDE_DIRS include
  LIBRARIES communication_lib
)

include_directories(
  ${catkin_INCLUDE_DIRS}
  ${Boost_INCLUDE_DIRS}
  include
)

add_library(communication_lib
  src/serial_comm.cpp
  src/network_comm.cpp
)

target_link_libraries(communication_lib
  ${catkin_LIBRARIES}
  ${Boost_LIBRARIES}
)

catkin_install_python(PROGRAMS
  scripts/serial_comm_node.py
  scripts/network_comm_node.py
  scripts/ros_bridge_node.py
  scripts/i2c_comm_node.py
  scripts/spi_comm_node.py
  scripts/serial_comm_tester.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
  FILES_MATCHING PATTERN "*.launch"
)

install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
  FILES_MATCHING PATTERN "*.yaml"
)