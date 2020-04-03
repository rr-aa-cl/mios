cmake_minimum_required(VERSION 2.8.3)
project(mios-event_publisher)

add_library(event_publisher SHARED src/event_publisher.cpp)

target_link_libraries(event_publisher cpp_utils)

install(TARGETS event_publisher DESTINATION ${CMAKE_SOURCE_DIR}/lib)
