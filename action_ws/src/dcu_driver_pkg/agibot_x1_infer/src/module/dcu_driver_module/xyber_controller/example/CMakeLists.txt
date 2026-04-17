# Get the current folder name
string(REGEX REPLACE ".*/\(.*\)" "\\1" CUR_DIR ${CMAKE_CURRENT_SOURCE_DIR})

# Targets
set(EXAMPLE_TARGETS
    canfd_forward_test
    canfd_receive_test
    canfd_raw_receive_test
    canfd_recv_test
)

# Add targets
foreach(TARGET ${EXAMPLE_TARGETS})
    add_executable(${TARGET} ${TARGET}.cpp)
    target_include_directories(
        ${TARGET}
        PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../xyber_api/include
    )
    target_link_libraries(${TARGET} PUBLIC xyber_controller)
    
    install(
        TARGETS ${TARGET}
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
        RUNTIME DESTINATION bin COMPONENT ${TARGET})
endforeach()