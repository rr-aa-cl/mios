configure_file(${CMAKE_SOURCE_DIR}/utils/mios.sh ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/bin/mios.sh COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/desk/desk_client.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/desk/desk_client.py COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/utils/udp_client.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/utils/udp_client.py COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/utils/ws_client.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/utils/ws_client.py COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/utils/rpc_client.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/utils/rpc_client.py COPYONLY)

file(COPY ${CMAKE_SOURCE_DIR}/ml_service DESTINATION ${CMAKE_SOURCE_DIR}/${PROJECT_NAME})
file(COPY ${CMAKE_SOURCE_DIR}/lib/plugins DESTINATION ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib)
