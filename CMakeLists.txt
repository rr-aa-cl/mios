cmake_minimum_required(VERSION 3.16)
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
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Werror -Wreturn-type -Wno-error=deprecated-declarations")
set (CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/CMake")
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
include(cotire)

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
    ${CMAKE_SOURCE_DIR}/manipulation_primitive/include
    ${CMAKE_SOURCE_DIR}/utils/include
    ${CMAKE_SOURCE_DIR}/plugins/include
    ${CMAKE_SOURCE_DIR}/panda/include
    ${CMAKE_SOURCE_DIR}/controller_pipeline/include
    ${CMAKE_SOURCE_DIR}/memory/include
    ${CMAKE_SOURCE_DIR}/portal/include)

set(PLUGINS mogen_p2p mogen_p2p_joint cntr_aic cntr_force cntr_joint_imp cntr_joint_var_imp cntr_mux cntr_nullsp_proj
    conv_vel2pose motion_error_cart virtual_cube virtual_walls_joint wave_variables)
link_directories(${CMAKE_SOURCE_DIR}/plugins/lib)

set(SOURCES core/src/core.cpp interface/src/interface.cpp manipulation_primitive/src/manipulation_primitive.cpp skill/src/skill.cpp task/src/task.cpp task/src/task_engine.cpp
    task/src/taskfactory.cpp task/src/taskobserver.cpp skill/src/skill_engine.cpp portal/src/portal.cpp panda/src/panda_body.cpp)
set(UTILS_SRC utils/src/actuator.cpp utils/src/percept.cpp utils/src/object.cpp utils/src/exceptions.cpp utils/src/results.cpp)
set(MEMORY_SRC memory/src/memory.cpp memory/src/lt_memory.cpp memory/src/st_memory.cpp memory/src/mongodb_client.cpp memory/src/parameters.cpp)
set(CONTROLLER_SRC controller_pipeline/src/cart_torque_pipeline.cpp controller_pipeline/src/joint_torque_pipeline.cpp controller_pipeline/src/cart_velocity_pipeline.cpp controller_pipeline/src/joint_velocity_pipeline.cpp)

set(SOURCES_PRIMITIVES manipulation_primitive/src/primitives/mp_basic.cpp manipulation_primitive/src/primitives/mp_basic_joint.cpp manipulation_primitive/src/primitives/nullprimitive.cpp)

file(GLOB SOURCES_SKILLS "skill/src/skills/*.cpp")
file(GLOB SOURCES_TASKS "task/src/tasks/*.cpp")
#file(GLOB SOURCES_PATTERN "led_pattern/src/patterns/*.cpp")

add_executable(mios main/src/mios.cpp ${SOURCES} ${MEMORY_SRC} ${UTILS_SRC} ${CONTROLLER_SRC} ${SOURCES_PRIMITIVES} ${SOURCES_SKILLS} ${SOURCES_TASKS} ${SOURCES_PATTERN})
#cotire(mios)

target_link_libraries(mios general ${PLUGINS} franka mongocxx bsoncxx boost_system SDL2 SDL2_mixer ssl crypto pthread
                            debug msrm_cpp_utils_dbg ssl crypto
                            optimized msrm_cpp_utils ssl crypto)

install(TARGETS mios DESTINATION ${CMAKE_SOURCE_DIR}/bin)
