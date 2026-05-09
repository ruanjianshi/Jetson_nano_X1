cmake_minimum_required(VERSION 3.0.2)
project(gpio_control)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  message_generation
)

find_package(Boost REQUIRED)

add_service_files(FILES GPIOControl.srv)
generate_messages(DEPENDENCIES std_msgs)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs message_runtime
  INCLUDE_DIRS include
  LIBRARIES gpio_control_lib
)

include_directories(
  ${catkin_INCLUDE_DIRS}
  ${Boost_INCLUDE_DIRS}
  include
)

add_library(gpio_control_lib
  src/gpio_manager.cpp
)

target_link_libraries(gpio_control_lib
  ${catkin_LIBRARIES}
  ${Boost_LIBRARIES}
)

catkin_install_python(PROGRAMS
  scripts/gpio_control_node.py
  scripts/gpio_test_node.py
  scripts/gpio_publisher_example.py
  scripts/gpio_subscriber_example.py
  scripts/gpio_service_client_example.py
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