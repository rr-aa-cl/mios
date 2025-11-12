configure_file(${CMAKE_SOURCE_DIR}/utils/mios.sh ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/bin/mios.sh COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/desk/deskapi.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/desk/deskapi.py COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/desk/keep_alive.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/desk/keep_alive.py COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/desk/config_loader.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/desk/config_loader.py COPYONLY)

configure_file(${CMAKE_SOURCE_DIR}/python/desk/mongodb_client.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/desk/mongodb_client.py COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/utils/udp_client.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/utils/udp_client.py COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/utils/ws_client.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/utils/ws_client.py COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/python/utils/rpc_client.py ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/python/utils/rpc_client.py COPYONLY)


configure_file(${CMAKE_SOURCE_DIR}/src/plugins/cntr_aic/libcntr_aic.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libcntr_aic.so COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/src/plugins/cntr_force/libcntr_force.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libcntr_force.so COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/src/plugins/cntr_joint_var_imp/libcntr_joint_var_imp.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libcntr_joint_var_imp.so COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/src/plugins/cntr_mux/libcntr_mux.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libcntr_mux.so COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/src/plugins/cntr_nullsp_proj/libcntr_nullsp_proj.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libcntr_nullsp_proj.so COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/src/plugins/conv_vel2pose/libconv_vel2pose.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libconv_vel2pose.so COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/src/plugins/mogen_p2p/libmogen_p2p.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libmogen_p2p.so COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/src/plugins/mogen_p2p_joint/libmogen_p2p_joint.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libmogen_p2p_joint.so COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/src/plugins/virtual_cube/libvirtual_cube.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libvirtual_cube.so COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/src/plugins/virtual_walls_joint/libvirtual_walls_joint.so ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib/plugins/libvirtual_walls_joint.so COPYONLY)

file(COPY ${CMAKE_SOURCE_DIR}/ml_service DESTINATION ${CMAKE_SOURCE_DIR}/${PROJECT_NAME})

file(COPY ${CMAKE_BINARY_DIR}/lib/boost DESTINATION ${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/lib)
