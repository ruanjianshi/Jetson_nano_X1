cmake_minimum_required(VERSION 3.0.2)
project(mcp2515_can_driver)

find_package(catkin REQUIRED COMPONENTS
  actionlib
  actionlib_msgs
  roscpp
  rospy
  std_msgs
  message_generation
)

add_action_files(
  DIRECTORY action
  FILES
  MCP2515CANComm.action
)

generate_messages(
  DEPENDENCIES
  std_msgs
  actionlib_msgs
)

catkin_package(
  CATKIN_DEPENDS actionlib actionlib_msgs roscpp rospy std_msgs message_runtime
)

include_directories(
  ${catkin_INCLUDE_DIRS}
  include
)

add_library(mcp2515_driver
  src/mcp2515_driver.cpp
)

add_executable(mcp2515_can_server_cpp
  src/mcp2515_can_server.cpp
)

add_executable(mcp2515_can_client_cpp
  src/mcp2515_can_client.cpp
)

add_dependencies(mcp2515_can_server_cpp ${${PROJECT_NAME}_EXPORTED_TARGETS})
add_dependencies(mcp2515_can_client_cpp ${${PROJECT_NAME}_EXPORTED_TARGETS})

target_link_libraries(mcp2515_can_server_cpp
  ${catkin_LIBRARIES}
  mcp2515_driver
)

target_link_libraries(mcp2515_can_client_cpp
  ${catkin_LIBRARIES}
)

catkin_install_python(PROGRAMS
  scripts/mcp2515_can_server.py
  scripts/mcp2515_can_client.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(TARGETS mcp2515_can_server_cpp mcp2515_can_client_cpp mcp2515_driver
  ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
