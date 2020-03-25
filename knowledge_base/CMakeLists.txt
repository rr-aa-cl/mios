cmake_minimum_required(VERSION 2.8.3)
project(mios-kb)

add_library(knowledge_base SHARED src/knowledge_base.cpp src/local_memory.cpp src/concepts.cpp)
target_link_libraries(knowledge_base cpp_utils parameter_server mongocxx bsoncxx)

install(TARGETS knowledge_base DESTINATION ${CMAKE_SOURCE_DIR}/lib)
