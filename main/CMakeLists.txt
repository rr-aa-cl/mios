cmake_minimum_required(VERSION 2.8.3)
project(mios-main)

add_executable(mios src/mios.cpp)

target_link_libraries(mios core task_handler cpp_utils interface)

install(TARGETS mios DESTINATION ${CMAKE_SOURCE_DIR}/bin)
