# Get the current folder name
string(REGEX REPLACE ".*/\(.*\)" "\\1" CUR_DIR ${CMAKE_CURRENT_SOURCE_DIR})

# Set target name
set(CUR_TARGET_NAME "xyber_controller")

# Set file collection
file(GLOB_RECURSE head_files ${CMAKE_CURRENT_SOURCE_DIR}/include/*.h)
file(GLOB_RECURSE src_files ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)

# Add target
add_library(${CUR_TARGET_NAME} STATIC)

# Set source file of target
target_sources(${CUR_TARGET_NAME} PRIVATE ${src_files})

# Set include path of target
target_include_directories(
  ${CUR_TARGET_NAME}
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Set link libraries of target
target_link_libraries(${CUR_TARGET_NAME} PRIVATE soem)

install(
  TARGETS ${CUR_TARGET_NAME}
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin COMPONENT ${CUR_TARGET_NAME})

# Install header files
install(
  DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/include/
  DESTINATION include/${CUR_TARGET_NAME}
  FILES_MATCHING
  PATTERN "*.h"
  EXCLUDE
  PATTERN "internal/*")