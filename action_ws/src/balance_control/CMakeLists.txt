cmake_minimum_required(VERSION 3.0.2)
project(balance_control)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  std_msgs
  sensor_msgs
  geometry_msgs
  nav_msgs
  control_msgs
  actionlib
  actionlib_msgs
  trajectory_msgs
  message_generation
  dcu_driver_pkg
)

find_package(Eigen3 REQUIRED)
find_package(yaml-cpp REQUIRED)

add_action_files(
  DIRECTORY action
  FILES
  BalanceControl.action
)

generate_messages(DEPENDENCIES std_msgs actionlib_msgs)

catkin_package(
  INCLUDE_DIRS include algorithms
  LIBRARIES balance_control_lib algorithms_lib hardware_params_lib
  CATKIN_DEPENDS
    roscpp
    std_msgs
    sensor_msgs
    geometry_msgs
    nav_msgs
    control_msgs
    actionlib
    actionlib_msgs
    trajectory_msgs
    message_runtime
  DEPENDS EIGEN3
)

include_directories(
  include
  algorithms
  ${catkin_INCLUDE_DIRS}
  ${EIGEN3_INCLUDE_DIRS}
  ${YAML_CPP_INCLUDE_DIRS}
)

# ========== 算法库 ==========
add_library(algorithms_lib
  algorithms/lqr_controller.cpp
  algorithms/vmc_controller.cpp
  algorithms/mpc_controller.cpp
  algorithms/adp_controller.cpp
)

add_dependencies(algorithms_lib ${catkin_EXPORTED_TARGETS})

target_link_libraries(algorithms_lib
  ${catkin_LIBRARIES}
  ${EIGEN3_LIBRARIES}
)

# ========== 硬件参数库 ==========
add_library(hardware_params_lib
  src/robot_hardware_params.cpp
)

add_dependencies(hardware_params_lib ${catkin_EXPORTED_TARGETS})

target_link_libraries(hardware_params_lib
  ${catkin_LIBRARIES}
  ${EIGEN3_LIBRARIES}
  ${YAML_CPP_LIBRARIES}
)

# ========== 平衡控制服务器库 ==========
add_library(balance_control_lib
  src/balance_control_server.cpp
)

add_dependencies(balance_control_lib ${catkin_EXPORTED_TARGETS})

target_link_libraries(balance_control_lib
  algorithms_lib
  hardware_params_lib
  ${catkin_LIBRARIES}
)

# ========== 可执行文件 ==========

# 平衡控制主节点 (Server + Client合一)
add_executable(balance_control_server
  src/balance_control_server.cpp
)

add_dependencies(balance_control_server ${catkin_EXPORTED_TARGETS})

target_link_libraries(balance_control_server
  algorithms_lib
  hardware_params_lib
  ${catkin_LIBRARIES}
)

# 机器人命令客户端
add_executable(robot_command_client
  src/robot_command_client.cpp
)

add_dependencies(robot_command_client ${catkin_EXPORTED_TARGETS})

target_link_libraries(robot_command_client
  balance_control_lib
  hardware_params_lib
  ${catkin_LIBRARIES}
)

# 测试节点
add_executable(balance_control_test
  src/balance_control_test.cpp
)

add_dependencies(balance_control_test ${catkin_EXPORTED_TARGETS})

target_link_libraries(balance_control_test
  balance_control_lib
  hardware_params_lib
  ${catkin_LIBRARIES}
  ${EIGEN3_LIBRARIES}
)

# Python scripts installation
catkin_install_python(PROGRAMS
  scripts/robot_command_client.py
  scripts/robot_keyboard_teleop.py
  scripts/robot_cli.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)