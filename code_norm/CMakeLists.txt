cmake_minimum_required(VERSION 3.16)
project(code_project VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

find_package(Threads REQUIRED)
find_package(spdlog REQUIRED)

option(CODE_PROJECT_BUILD_TESTS "Build unit tests" ON)
option(CODE_PROJECT_ENABLE_SANITIZERS "Enable sanitizers in Debug" ON)

add_library(code_project_core INTERFACE)
target_include_directories(code_project_core INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

add_library(code_project::core ALIAS code_project_core)

add_library(code_project INTERFACE)
target_link_libraries(code_project INTERFACE code_project_core)
add_library(code_project::project ALIAS code_project)

file(GLOB_RECURSE CODE_PROJECT_HEADERS
    RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
    "include/*.h"
)

set_target_properties(code_project PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
)

include(CTest)
