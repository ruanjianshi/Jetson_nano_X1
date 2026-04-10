cmake_minimum_required(VERSION 3.0.2)
project(maita_can_comm)

find_package(catkin REQUIRED COMPONENTS
  actionlib
  actionlib_msgs
  roscpp
  rospy
  std_msgs
)

add_action_files(
  DIRECTORY action
  FILES
  CANComm.action
)

generate_messages(
  DEPENDENCIES
  std_msgs
  actionlib_msgs
)

catkin_package(
  CATKIN_DEPENDS actionlib actionlib_msgs roscpp rospy std_msgs
)

include_directories(
  ${catkin_INCLUDE_DIRS}
  ${CMAKE_CURRENT_SOURCE_DIR}/usbcan_ii_libusb_aarch64
)

include_directories(
  ${catkin_INCLUDE_DIRS}
  ${CMAKE_CURRENT_SOURCE_DIR}/usbcan_ii_libusb_aarch64
  ${CMAKE_CURRENT_SOURCE_DIR}/src
)

add_executable(can_comm_maita_server_cpp src/can_comm_maita_server.cpp)
target_link_libraries(can_comm_maita_server_cpp
  ${catkin_LIBRARIES}
  ${CMAKE_CURRENT_SOURCE_DIR}/usbcan_ii_libusb_aarch64/libusbcan.so
  pthread
  dl
)
add_dependencies(can_comm_maita_server_cpp ${PROJECT_NAME}_generate_messages_cpp)

add_executable(can_comm_maita_client_cpp src/can_comm_maita_client.cpp)
target_link_libraries(can_comm_maita_client_cpp
  ${catkin_LIBRARIES}
)
add_dependencies(can_comm_maita_client_cpp ${PROJECT_NAME}_generate_messages_cpp)

catkin_install_python(PROGRAMS
  scripts/can_comm_maita_server.py
  scripts/can_comm_client.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(TARGETS can_comm_maita_server_cpp can_comm_maita_client_cpp
  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

install(DIRECTORY usbcan_ii_libusb_aarch64/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/usbcan_ii_libusb_aarch64
)