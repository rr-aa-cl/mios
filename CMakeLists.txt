cmake_minimum_required(VERSION 3.16)

find_program(CCACHE_PROGRAM ccache)
if(CCACHE_PROGRAM)
    set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE "${CCACHE_PROGRAM}")
endif()

project(mios
    LANGUAGES CXX
    )


if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()
set(CMAKE_CXX_FLAGS_DEBUG "-g")
set(CMAKE_CXX_FLAGS_RELEASE "-O3")
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_LINK_DEPENDS_NO_SHARED)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Werror=return-type -Werror=uninitialized -Wno-error=deprecated-declarations -Wno-error=unused-result")
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_PREFIX_PATH ${CMAKE_SOURCE_DIR}/third_party/share/cmake;${CMAKE_SOURCE_DIR}/third_party/lib/cmake)

find_package(Franka REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(pybind11 REQUIRED)
find_package(libmongocxx-static REQUIRED)
find_package(libbsoncxx-static REQUIRED)
#find_package(PythonLibs REQUIRED)

find_package(roscpp REQUIRED
    std_srvs REQUIRED
    message_generation REQUIRED)


include_directories(${roscpp_INCLUDE_DIRS})
include_directories(${std_srvs_INCLUDE_DIRS})
include_directories(${message_generation_INCLUDE_DIRS})
include_directories(${CMAKE_SOURCE_DIR}/third_party/include)
include_directories(${LIBMONGOCXX_STATIC_INCLUDE_DIRS})
include_directories(${LIBBSONCXX_STATIC_INCLUDE_DIRS})

include_directories(
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/skill/include
    ${CMAKE_SOURCE_DIR}/task/include
    ${CMAKE_SOURCE_DIR}/interface/include
    ${CMAKE_SOURCE_DIR}/manipulation_primitive/include
    ${CMAKE_SOURCE_DIR}/utils/include
    ${CMAKE_SOURCE_DIR}/plugins/include
    ${CMAKE_SOURCE_DIR}/panda/include
    ${CMAKE_SOURCE_DIR}/controller_pipeline/include
    ${CMAKE_SOURCE_DIR}/safety/include
    ${CMAKE_SOURCE_DIR}/memory/include
    ${CMAKE_SOURCE_DIR}/portal/include
    ${CMAKE_SOURCE_DIR}/libraries/include
    ${CMAKE_SOURCE_DIR}/ros_workspace/devel/include)

link_directories(${CMAKE_SOURCE_DIR}/third_party/lib)

set(PLUGINS mogen_p2p mogen_p2p_joint cntr_aic cntr_force cntr_joint_imp cntr_joint_var_imp cntr_mux cntr_nullsp_proj
    conv_vel2pose motion_error_cart virtual_cube virtual_walls_joint)
link_directories(${CMAKE_SOURCE_DIR}/lib/plugins)

set(SOURCES core/src/core.cpp interface/src/interface.cpp manipulation_primitive/src/manipulation_primitive.cpp manipulation_primitive/src/primitive_strategy.cpp
    skill/src/skill.cpp task/src/task.cpp task/src/task_engine.cpp panda/src/softhand2.cpp panda/src/qbmove_communications.cpp
    task/src/taskfactory.cpp task/src/taskobserver.cpp skill/src/skill_engine.cpp portal/src/portal.cpp panda/src/panda_body.cpp interface/src/ros_node.cpp)
set(UTILS_SRC utils/src/actuator.cpp utils/src/percept.cpp utils/src/object.cpp utils/src/exceptions.cpp utils/src/results.cpp utils/src/event.cpp)
set(MEMORY_SRC memory/src/memory.cpp memory/src/lt_memory.cpp memory/src/st_memory.cpp memory/src/mongodb_client.cpp memory/src/parameters.cpp)
set(CONTROLLER_SRC controller_pipeline/src/cart_torque_pipeline.cpp controller_pipeline/src/joint_torque_pipeline.cpp controller_pipeline/src/cart_velocity_pipeline.cpp
    controller_pipeline/src/joint_velocity_pipeline.cpp controller_pipeline/src/null_pipeline.cpp)
set(SAFETY_SRC safety/src/velocity_walls.cpp safety/src/virtual_cube.cpp safety/src/virtual_joint_walls.cpp)

#set(SOURCES_PRIMITIVES manipulation_primitive/src/primitives/mp_basic.cpp manipulation_primitive/src/primitives/mp_basic_joint.cpp manipulation_primitive/src/primitives/nullprimitive.cpp)

file(GLOB SOURCES_SKILLS "libraries/src/skills/*.cpp")
file(GLOB SOURCES_TASKS "libraries//src/tasks/*.cpp")
file(GLOB SOURCES_STRATEGIES "libraries/src/strategies/*.cpp")
#file(GLOB SOURCES_PATTERN "led_pattern/src/patterns/*.cpp")

add_executable(mios main/src/mios.cpp ${SOURCES} ${MEMORY_SRC} ${UTILS_SRC} ${CONTROLLER_SRC} ${SAFETY_SRC} ${SOURCES_STRATEGIES} ${SOURCES_SKILLS} ${SOURCES_TASKS} ${SOURCES_PATTERN})
#cotire(mios)

set_target_properties(mios PROPERTIES UNITY_BUILD ON)
target_precompile_headers(mios PRIVATE ${CMAKE_SOURCE_DIR}/utils/include/utils/pch.hpp)

target_link_libraries(mios general ${PLUGINS} franka mongocxx-static ${LIBMONGOCXX_STATIC_LIBRARIES} stdc++fs ${roscpp_LIBRARIES} pybind11::embed
                            debug msrm_cpp_utils_dbg ssl crypto pthread boost_system
                            optimized msrm_cpp_utils ssl crypto pthread boost_system)

install(TARGETS mios DESTINATION ${CMAKE_SOURCE_DIR}/bin)
