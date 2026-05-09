cmake_minimum_required(VERSION 3.0.2)
project(pc_control_ui)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

# Find Qt5
find_package(Qt5 REQUIRED COMPONENTS Widgets)

# Find ROS (use catkin to locate roscpp, std_msgs)
find_package(catkin REQUIRED COMPONENTS roscpp std_msgs)

# Include ROS + Qt headers
include_directories(
    ${catkin_INCLUDE_DIRS}
    ${Qt5Widgets_INCLUDE_DIRS}
)

add_executable(pc_control_ui
    src/main.cpp
    src/main_window.cpp
    src/main_window.h
)

target_link_libraries(pc_control_ui
    ${catkin_LIBRARIES}
    Qt5::Widgets
)

# Look for jsoncpp; if not found, try bundled fallback
find_package(PkgConfig)
if(PkgConfig_FOUND)
    pkg_check_modules(JSONCPP jsoncpp)
endif()
if(JSONCPP_FOUND)
    target_include_directories(pc_control_ui PRIVATE ${JSONCPP_INCLUDE_DIRS})
    target_link_libraries(pc_control_ui ${JSONCPP_LIBRARIES})
else()
    message(STATUS "jsoncpp not found via pkgconfig — ensure it is installed (sudo apt install libjsoncpp-dev)")
endif()
