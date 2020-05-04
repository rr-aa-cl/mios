cmake_minimum_required(VERSION 3.10.2)
project(mios-telemetry)

add_library(telemetry SHARED src/telemetry_udp.cpp)
target_link_libraries(telemetry msrm_cpp_utils boost_thread boost_chrono knowledge_base)

install(TARGETS telemetry DESTINATION ${CMAKE_SOURCE_DIR}/lib)
