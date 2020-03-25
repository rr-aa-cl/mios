cmake_minimum_required(VERSION 2.8.3)
project(mios-interface)

#add_library(interface SHARED src/rpc_server.cpp)
add_library(parameter_server SHARED src/parameter_server.cpp)
add_library(sim_interface SHARED src/sim_interface.cpp)
#add_library(ws_server SHARED src/ws_server.cpp)
add_library(interface SHARED src/interface.cpp)

target_link_libraries(interface core task_handler cpp_utils)
#target_link_libraries(ws_server core task_handler cpp_utils knowledge_base ${ACTIVE_TASKS} boost_system pthread ${OPENSSL_LIBRARIES})
#target_link_libraries(ws_server core task_handler cpp_utils knowledge_base ${ACTIVE_TASKS} boost_system pthread ${OPENSSL_LIBRARIES})

install(TARGETS parameter_server DESTINATION ${CMAKE_SOURCE_DIR}/lib)
install(TARGETS interface DESTINATION ${CMAKE_SOURCE_DIR}/lib)
install(TARGETS sim_interface DESTINATION ${CMAKE_SOURCE_DIR}/lib)
#install(TARGETS ws_server DESTINATION ${CMAKE_SOURCE_DIR}/lib)
