cmake_minimum_required(VERSION 3.0.2)
project(distributed_comm)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  std_msgs
  sensor_msgs
)

find_package(PkgConfig)
if(PkgConfig_FOUND)
  pkg_check_modules(JSONCPP jsoncpp)
endif()

catkin_package(
  CATKIN_DEPENDS roscpp rospy std_msgs sensor_msgs
)

include_directories(${catkin_INCLUDE_DIRS})
if(JSONCPP_FOUND)
  include_directories(${JSONCPP_INCLUDE_DIRS})
endif()

# C++ nodes
add_executable(jetson_bridge src/jetson_bridge.cpp)
target_link_libraries(jetson_bridge ${catkin_LIBRARIES})

add_executable(pc_bridge src/pc_bridge.cpp)
target_link_libraries(pc_bridge ${catkin_LIBRARIES})

add_executable(rate_tester src/rate_tester.cpp)
target_link_libraries(rate_tester ${catkin_LIBRARIES})

add_executable(jetson_controller src/jetson_controller.cpp)
target_link_libraries(jetson_controller ${catkin_LIBRARIES})
if(JSONCPP_FOUND)
  target_link_libraries(jetson_controller ${JSONCPP_LIBRARIES})
endif()

# Python scripts
catkin_install_python(PROGRAMS
  test/scripts/camera_publisher.py
  test/scripts/distributed_yolo_server.py
  test/scripts/jetson_display.py
  test/pc_control_test/scripts/test_commands.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
