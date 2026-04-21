cmake_minimum_required(VERSION 3.0.2)
project(dcu_driver_pkg)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  std_msgs
  sensor_msgs
  geometry_msgs
  actionlib_msgs
  actionlib
  message_generation
)

add_action_files(
  DIRECTORY action
  FILES
  DCUControl.action
)

add_message_files(
  DIRECTORY msg
  FILES
  MotorCommand.msg
)

generate_messages(
  DEPENDENCIES
  actionlib_msgs
  std_msgs
  sensor_msgs
  geometry_msgs
)

catkin_package(
  INCLUDE_DIRS 
    include
    agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/xyber_api/include
    agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem
    agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem
    agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/oshw/linux
    agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/osal/linux
    agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/osal
  LIBRARIES 
    soem
    xyber_controller
  CATKIN_DEPENDS 
    roscpp 
    std_msgs 
    sensor_msgs 
    geometry_msgs 
    actionlib_msgs
    message_runtime
  DEPENDS
)

include_directories(
  include
  ${catkin_INCLUDE_DIRS}
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/xyber_api/include
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/oshw/linux
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/osal/linux
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/osal
)

set(SOEM_SOURCES
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem/ethercatbase.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem/ethercatcoe.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem/ethercatconfig.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem/ethercatdc.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem/ethercateoe.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem/ethercatfoe.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem/ethercatmain.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem/ethercatprint.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/soem/ethercatsoe.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/oshw/linux/nicdrv.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/oshw/linux/oshw.c
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/third_party/soem/osal/linux/osal.c
)

set(XYBER_API_SOURCES
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/xyber_api/src/comm_utils.cpp
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/xyber_api/src/dcu.cpp
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/xyber_api/src/ethercat_manager.cpp
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/xyber_api/src/power_flow.cpp
  agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/xyber_api/src/xyber_controller.cpp
)

add_library(soem STATIC ${SOEM_SOURCES})
target_compile_options(soem PRIVATE -fPIC)

add_library(xyber_controller STATIC ${XYBER_API_SOURCES})
target_link_libraries(xyber_controller PRIVATE soem)
target_compile_options(xyber_controller PRIVATE -fPIC)

add_executable(dcu_driver_server src/dcu_driver_server.cpp)
target_link_libraries(dcu_driver_server
  soem
  xyber_controller
  ${catkin_LIBRARIES}
  Threads::Threads
)
target_compile_options(dcu_driver_server PRIVATE -fPIC)

add_executable(dcu_driver_client src/dcu_driver_client.cpp)
target_link_libraries(dcu_driver_client
  soem
  xyber_controller
  ${catkin_LIBRARIES}
  Threads::Threads
)
target_compile_options(dcu_driver_client PRIVATE -fPIC)

add_executable(ethercat_scan src/ethercat_scan.cpp)
target_link_libraries(ethercat_scan soem pthread)
target_compile_options(ethercat_scan PRIVATE)

add_executable(dcu_can_test src/dcu_can_test.cpp)
target_link_libraries(dcu_can_test
  soem
  xyber_controller
  ${catkin_LIBRARIES}
  Threads::Threads
)
target_compile_options(dcu_can_test PRIVATE -fPIC)

add_executable(dcu_control_node src/dcu_control_node.cpp)
target_link_libraries(dcu_control_node
  soem
  xyber_controller
  ${catkin_LIBRARIES}
  Threads::Threads
)
target_compile_options(dcu_control_node PRIVATE -fPIC)

install(TARGETS soem xyber_controller dcu_driver_server dcu_control_node ethercat_scan dcu_can_test
  ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
)

install(DIRECTORY include/
  DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
)

install(DIRECTORY agibot_x1_infer/src/module/dcu_driver_module/cfg/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/cfg
  USE_SOURCE_PERMISSIONS
  FILES_MATCHING PATTERN "*.yaml"
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
