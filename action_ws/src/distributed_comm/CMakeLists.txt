cmake_minimum_required(VERSION 3.0.2)
project(distributed_comm)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  std_msgs
  sensor_msgs
)

catkin_package(
  CATKIN_DEPENDS roscpp rospy std_msgs sensor_msgs
)

include_directories(${catkin_INCLUDE_DIRS})

# C++ nodes
add_executable(jetson_bridge src/jetson_bridge.cpp)
target_link_libraries(jetson_bridge ${catkin_LIBRARIES})

add_executable(pc_bridge src/pc_bridge.cpp)
target_link_libraries(pc_bridge ${catkin_LIBRARIES})

add_executable(rate_tester src/rate_tester.cpp)
target_link_libraries(rate_tester ${catkin_LIBRARIES})

# Python scripts
catkin_install_python(PROGRAMS
  test/scripts/camera_publisher.py
  test/scripts/distributed_yolo_server.py
  test/scripts/jetson_display.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
