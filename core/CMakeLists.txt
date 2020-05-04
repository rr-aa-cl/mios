cmake_minimum_required(VERSION 3.10.2)
project(mios-core)

find_package(Franka REQUIRED)

add_library(core SHARED src/core.cpp)
target_link_libraries(core msrm_cpp_utils skill led_pattern knowledge_base telemetry sim_interface franka boost_thread boost_system conv_vel2pose cntr_force
    cntr_aic cntr_joint_var_imp cntr_mux virtual_cube virtual_walls_joint cntr_nullsp_proj SDL2 SDL2_mixer ssl crypto pthread)

install(TARGETS core DESTINATION ${CMAKE_SOURCE_DIR}/lib)
