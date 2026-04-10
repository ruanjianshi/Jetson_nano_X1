cmake_minimum_required(VERSION 3.0.2)
project(common_utils)

find_package(catkin REQUIRED COMPONENTS
  rospy
)

catkin_package(
  CATKIN_DEPENDS rospy
  INCLUDE_DIRS include
  LIBRARIES common_utils_lib
)

include_directories(
  ${catkin_INCLUDE_DIRS}
  include
)

add_library(common_utils_lib
  src/logger.cpp
  src/config_loader.cpp
)

target_link_libraries(common_utils_lib ${catkin_LIBRARIES})

catkin_install_python(PROGRAMS
  scripts/logger_utils.py
  scripts/config_loader.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)