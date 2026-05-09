cmake_minimum_required(VERSION 3.10)
project(MultithreadingDev)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pthread")

include_directories(${CMAKE_SOURCE_DIR}/include)

file(GLOB_RECURSE SOURCES 
    "src/*.cpp"
)

add_executable(multithread_test ${SOURCES})

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    target_compile_options(multithread_test PRIVATE -Wall -Wextra -pthread)
endif()

target_link_libraries(multithread_test PRIVATE pthread)