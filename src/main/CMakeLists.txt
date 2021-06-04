add_executable(mios src/mios.cpp)

target_link_libraries(mios mios::project_options)

install(TARGETS mios DESTINATION ${CMAKE_SOURCE_DIR}/bin)
