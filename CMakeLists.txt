cmake_minimum_required(VERSION 3.10.2)
project(mios
    LANGUAGES CXX
    )


set(CMAKE_BUILD_TYPE Release)
set(CMAKE_CXX_FLAGS_DEBUG "-g")
set(CMAKE_CXX_FLAGS_RELEASE "-O3")
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_LINK_DEPENDS_NO_SHARED)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Werror -Wreturn-type -Wno-error=deprecated-declarations")
#set(CMAKE_UNITY_BUILD ON)

find_package(Eigen3 REQUIRED)
find_package(libmongocxx REQUIRED)
find_package(libbsoncxx REQUIRED)
include_directories(${LIBMONGOCXX_INCLUDE_DIRS})
include_directories(${LIBBSONCXX_INCLUDE_DIRS})

include_directories(
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/skill/include
    ${CMAKE_SOURCE_DIR}/task/include
    ${CMAKE_SOURCE_DIR}/interface/include
    ${CMAKE_SOURCE_DIR}/led_pattern/include
    ${CMAKE_SOURCE_DIR}/led_pattern/patterns
    ${CMAKE_SOURCE_DIR}/manipulation_primitive/include
    ${CMAKE_SOURCE_DIR}/knowledge_base/include
    ${CMAKE_SOURCE_DIR}/telemetry/include
    ${CMAKE_SOURCE_DIR}/utils/include
    ${CMAKE_SOURCE_DIR}/event_publisher/include
    ${CMAKE_SOURCE_DIR}/cpp/include)

file(STRINGS ${CMAKE_SOURCE_DIR}/config/active_mp ACTIVE_MP)
file(STRINGS ${CMAKE_SOURCE_DIR}/config/active_skills ACTIVE_SKILLS)
file(STRINGS ${CMAKE_SOURCE_DIR}/config/active_tasks ACTIVE_TASKS)
file(STRINGS ${CMAKE_SOURCE_DIR}/config/active_patterns ACTIVE_LED_PATTERNS)

add_subdirectory(plugins/mogen_p2p)
include_directories(${mogen_p2p_INCLUDE_DIRS})
link_directories(${mogen_p2p_LIBRARIES})

add_subdirectory(plugins/mogen_p2p_joint)
include_directories(${mogen_p2p_joint_INCLUDE_DIRS})
link_directories(${mogen_p2p_joint_LIBRARIES})

add_subdirectory(plugins/cntr_joint_var_imp)
include_directories(${cntr_joint_var_imp_INCLUDE_DIRS})
link_directories(${cntr_joint_var_imp_LIBRARIES})

add_subdirectory(plugins/cntr_aic)
include_directories(${cntr_aic_INCLUDE_DIRS})
link_directories(${cntr_aic_LIBRARIES})

add_subdirectory(plugins/cntr_force)
include_directories(${cntr_force_INCLUDE_DIRS})
link_directories(${cntr_force_LIBRARIES})

add_subdirectory(plugins/cntr_mux)
include_directories(${cntr_mux_INCLUDE_DIRS})
link_directories(${cntr_mux_LIBRARIES})

add_subdirectory(plugins/conv_vel2pose)
include_directories(${conv_vel2pose_INCLUDE_DIRS})
link_directories(${conv_vel2pose_LIBRARIES})

add_subdirectory(plugins/motion_error_cart)
include_directories(${motion_error_cart_INCLUDE_DIRS})
link_directories(${motion_error_cart_LIBRARIES})

add_subdirectory(plugins/virtual_cube)
include_directories(${virtual_cube_INCLUDE_DIRS})
link_directories(${virtual_cube_LIBRARIES})

add_subdirectory(plugins/virtual_walls_joint)
include_directories(${virtual_walls_joint_INCLUDE_DIRS})
link_directories(${virtual_walls_joint_LIBRARIES})

add_subdirectory(plugins/cntr_nullsp_proj)
include_directories(${cntr_nullsp_proj_INCLUDE_DIRS})
link_directories(${cntr_nullsp_proj_LIBRARIES})

add_subdirectory(plugins/wave_variables)
include_directories(${wave_variables_INCLUDE_DIRS})
link_directories(${wave_variables_LIBRARIES})

add_subdirectory(
    led_pattern
    )
add_subdirectory(
    manipulation_primitive
    )
add_subdirectory(
    skill
    )
add_subdirectory(
    core
    )

add_subdirectory(
    task
    )

add_subdirectory(
    knowledge_base
    )
add_subdirectory(
    telemetry
    )
add_subdirectory(
    interface
    )
add_subdirectory(
    event_publisher
    )
add_subdirectory(
    main
    )
