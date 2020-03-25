cmake_minimum_required(VERSION 3.10.2)
project(mios-cm)

add_library(collective_module SHARED src/collective_module.cpp)
target_link_libraries(collective_module cpp_utils boost_thread boost_chrono knowledge_base)

install(TARGETS collective_module DESTINATION ${CMAKE_SOURCE_DIR}/lib)
