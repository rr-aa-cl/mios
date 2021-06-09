# Copyright (c) 2018 - present, Lars Johannsmeier
# All rights reserved.
# contact: lars.johannsmeier@tum.de

cmake_minimum_required(VERSION 3.16...3.20)

set(PROJECT_VERSION_MAJOR 0)
set(PROJECT_VERSION_MINOR 12)
set(PROJECT_VERSION_PATCH 2)
set(PROJECT_VERSION ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH})

project(mios VERSION ${PROJECT_VERSION}
    DESCRIPTION "Machine Intelligence Operating System (for Franka Emika Panda arms)"
    LANGUAGES CXX
    )

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    message(STATUS "Setting build type to 'Release' as none was specified.")
    set(CMAKE_BUILD_TYPE
        Release
        CACHE STRING "Choose the type of build." FORCE)
    # Set the possible values of build type for cmake-gui, ccmake
    set_property(
        CACHE CMAKE_BUILD_TYPE
        PROPERTY STRINGS
        "Debug"
        "Release"
        "MinSizeRel"
        "RelWithDebInfo")
endif()

include(cmake/ApplyModuleOptions.cmake)
include(cmake/Conan.cmake)
include(cmake/Doxygen.cmake)
include(cmake/PreventInSourceBuilds.cmake)
include(cmake/StaticAnalyzers.cmake)

option(ONLY_COVERAGE "Build only tests necessary for coverage" OFF)
option(LIBCPP "Build with libc++" OFF)
option(ENABLE_COVERAGE "Enable coverage reporting for gcc/clang" OFF)
option(ENABLE_ASAN "Enable address sanitizer" OFF)
option(BUILD_SHARED_LIBS "Enable compilation of shared libraries" OFF)
option(ENABLE_TESTING "Enable the building of the test" OFF)
option(ENABLE_CLANG_TIDY "Enable testing with clang-tidy" OFF)
option(ENABLE_CPPCHECK "Enable testing with cppcheck" OFF)
option(ENABLE_INCLUDE_WHAT_YOU_USE "Enable static analysis with include-what-you-use" OFF)
option(SIMPLE_BUILD "Build the project as minimally as possible" OFF)
option(BUILD_DOC "Build the project's documentation" OFF)
option(FORCE_COLORED_OUTPUT "Always produce ANSI-colored output (GNU/Clang only)." OFF)
option(DEBUG_LOGGING "Enabling debug logging" OFF)
option(ENABLE_IPO "Enable Interprocedural Optimization, aka Link Time Optimization (LTO)" OFF)
option(ENABLE_PCH "Enable Precompiled Headers" OFF)
option(ENABLE_UNITY_BUILD "Enable unity build" OFF)

add_library(${PROJECT_NAME}_project_warnings INTERFACE)
add_library(${PROJECT_NAME}_project_options INTERFACE)
add_library(${PROJECT_NAME}_project_deps INTERFACE)

target_compile_features(${PROJECT_NAME}_project_options
    INTERFACE
    cxx_std_17)

if(ENABLE_PCH)
    target_precompile_headers(
        ${PROJECT_NAME}_project_options
        INTERFACE
        ${CMAKE_SOURCE_DIR}/include/commons/pch.hpp
        )
endif()

target_compile_options(${PROJECT_NAME}_project_warnings
    INTERFACE
    #    -Wall
    #    -Wextra
    #    -Wshadow
    #    -Wnon-virtual-dtor
    #    -Wold-style-cast
    #    -Wcast-align
    #    -Wunused
    #    -Woverloaded-virtual
    #    -Wpedantic
    #    -Wconversion
    -Wsign-conversion
    -Wnull-dereference
    #    -Wdouble-promotion
    #    -Wformat=2
    -Wreturn-type
    -Wuninitialized
    )

if(ONLY_COVERAGE OR ENABLE_COVERAGE)
    target_compile_options(${PROJECT_NAME}_project_options INTERFACE --coverage -O0 -g)
    target_link_libraries(${PROJECT_NAME}_project_options INTERFACE --coverage)
endif()

if(ENABLE_ASAN)
    target_compile_options(${PROJECT_NAME}_project_options INTERFACE -fsanitize=address)
    target_link_libraries(${PROJECT_NAME}_project_options INTERFACE -fsanitize=address)
endif()

# some GCC specific warnings. These flags are added only if the used compiler is GCC.
if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
    target_compile_options(${PROJECT_NAME}_project_warnings
        INTERFACE
        #        -Wmisleading-indentation
        #        -Wduplicated-cond
        #        -Wlogical-op
        #        -Wuseless-cast
        )
    target_link_libraries(${PROJECT_NAME}_project_options INTERFACE stdc++fs)
endif()

if (${FORCE_COLORED_OUTPUT})
    if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
        target_compile_options (${PROJECT_NAME}_project_options INTERFACE -fdiagnostics-color=always)
    elseif ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
        target_compile_options (${PROJECT_NAME}_project_options INTERFACE -fcolor-diagnostics)
    endif ()
endif ()

find_program(CCACHE ccache)
if(CCACHE)
    set(CMAKE_CXX_COMPILER_LAUNCHER ${CCACHE})
    set(CMAKE_CUDA_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
endif()


include(cmake/FetchContent.cmake)


add_library(${PROJECT_NAME}::${PROJECT_NAME}_project_options ALIAS ${PROJECT_NAME}_project_options)
add_library(${PROJECT_NAME}::${PROJECT_NAME}_project_warnings ALIAS ${PROJECT_NAME}_project_warnings)
add_library(${PROJECT_NAME}::${PROJECT_NAME}_project_deps ALIAS ${PROJECT_NAME}_project_deps)

target_link_libraries(${PROJECT_NAME}_project_deps
    INTERFACE
    CONAN_PKG::spdlog
    )

add_subdirectory(src)

message("#########################################")
    message("\t \t Summary")
    message("#########################################")
        message("Build type:       \t ${CMAKE_BUILD_TYPE}")
        message("Install prefix:   \t ${CMAKE_INSTALL_PREFIX}")
        message("Testing enabled:  \t ${ENABLE_TESTING}")
        message("Clang-tidy:       \t ${ENABLE_CLANG_TIDY}")
        message("Cppcheck:         \t ${ENABLE_CPPCHECK}")
        message("Compiler:         \t ${CMAKE_CXX_COMPILER_ID}")
        message("Sanitizers:       \t ${ENABLE_ASAN}")
        message("Shared libs:      \t ${BUILD_SHARED_LIBS}")
        message("Build libcpp:     \t ${LIBCPP}")
        message("CCache executable:\t ${CCACHE}")
        message("PCH:              \t ${ENABLE_PCH}")
        message("IPO:              \t ${ENABLE_IPO}")
        message("Unity build:      \t ${ENABLE_UNITY_BUILD}")
        message("Building doc:     \t ${BUILD_DOC}")
        message("------------------------------------------")
        message("Version:          \t ${PROJECT_VERSION}")
        message("########################################")


# Copyright (c) 2018 - present, Lars Johannsmeier
# All rights reserved.
# contact: lars.johannsmeier@tum.de
#cmake_minimum_required(VERSION 3.16...3.20)

#include(cmake/utils.cmake)
#get_mios_version()

#project(mios VERSION ${MIOS_VERSION}
#                 DESCRIPTION "Machine Intelligence Operating System (for Franka Emika Panda arms)"
#                 LANGUAGES CXX)

#if(NOT EXISTS "${CMAKE_SOURCE_DIR}/cmake/conan.cmake")
#    message(STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan")
#    file(DOWNLOAD  "https://raw.githubusercontent.com/conan-io/cmake-conan/master/conan.cmake"
#        "${CMAKE_SOURCE_DIR}/cmake/conan.cmake")
#endif()
#include(${CMAKE_SOURCE_DIR}/cmake/conan.cmake)

#conan_check(REQUIRED)
#conan_cmake_run(
#    CONANFILE
#    conanfile.txt
#    BASIC_SETUP
#    CONAN_COMMAND
#    ${CONAN_CMD}
#    CMAKE_TARGETS
#    BUILD
#    missing)
#include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake) # conanbuildinfo.cmake is file generated by the cmake generator.
#conan_basic_setup()

#find_package(Eigen3 REQUIRED)
#find_package(PythonLibsNew REQUIRED)

#find_program(CCACHE_PROGRAM ccache)
#if(CCACHE_PROGRAM)
#    set(CMAKE_CXX_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
#    set(CMAKE_CUDA_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
#endif()

#if(ENABLE_CPPCHECK)
#    find_program(CPPCHECK cppcheck)
#    if(CPPCHECK)
#    set(CMAKE_CXX_CPPCHECK
#        ${CPPCHECK}
#        --suppress=syntaxError
#        --enable=all
#        --inconclusive)
#    else()
#    message(SEND_ERROR "cppcheck requested but executable not found")
#    endif()
#endif()

#if(ENABLE_CLANG_TIDY)
#    find_program(CLANGTIDY clang-tidy)
#    if(CLANGTIDY)
#    set(CMAKE_CXX_CLANG_TIDY ${CLANGTIDY})
#    else()
#    message(SEND_ERROR "clang-tidy requested but executable not found")
#    endif()
#endif()



#if(NOT CMAKE_BUILD_TYPE)
#    set(CMAKE_BUILD_TYPE Release)
#endif()

#set(CMAKE_CXX_FLAGS_DEBUG "-g")
#set(CMAKE_CXX_FLAGS_RELEASE "-O3")
#set(CMAKE_CXX_STANDARD 17)
#set(CMAKE_CXX_STANDARD_REQUIRED ON)
#set(CMAKE_POSITION_INDEPENDENT_CODE ON)
#set(CMAKE_LINK_DEPENDS_NO_SHARED)
#set(CMAKE_DEBUG_POSTFIX _dbg)
#set(CMAKE_EXPORT_COMPILE_COMMANDS On)
#set(CMAKE_PREFIX_PATH ${CMAKE_SOURCE_DIR}/extern/lib/cmake)
#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Werror=return-type -Werror=uninitialized -Wno-error=deprecated-declarations -Wno-error=unused-result")

#set(CMAKE_CXX_EXTENSIONS OFF)
#set(CMAKE_VERBOSE_MAKEFILE ON)

#add_compile_options(-std=c++17)
#if (CMAKE_CXX_COMPILER_ID MATCHES "Clang")
#    add_compile_options(-Wthread-safety)
#endif()

#if(CMAKE_BUILD_TYPE MATCHES Release)
#    include(${CMAKE_SOURCE_DIR}/build/release/conanbuildinfo.cmake)
#elseif(CMAKE_BUILD_TYPE MATCHES Debug)
#    include(${CMAKE_SOURCE_DIR}/build/debug/conanbuildinfo.cmake)
#endif()

#if(NOT TARGET Eigen3::Eigen3)
#  add_library(Eigen3::Eigen3 INTERFACE IMPORTED)
#  set_target_properties(Eigen3::Eigen3 PROPERTIES
#    INTERFACE_INCLUDE_DIRECTORIES ${EIGEN3_INCLUDE_DIRS}
#    INTERFACE_COMPILE_DEFINITIONS "${EIGEN3_DEFINITIONS}"
#  )
#endif()



#include(FetchContent)
#set(FETCHCONTENT_QUIET OFF)
#set(FETCHCONTENT_BASE_DIR ${CMAKE_SOURCE_DIR}/_deps)
#include(cmake/extern.cmake)

#find_package(roscpp REQUIRED
#    std_srvs REQUIRED
#    message_generation REQUIRED)


#option(MINIMAL_BUILD "Build with minimal set of skills, tasks and strategies" OFF)

#include_directories(${PYTHON_INCLUDE_DIRS})
#include_directories(${CONAN_INCLUDE_DIRS})
#include_directories(${roscpp_INCLUDE_DIRS})
#include_directories(${std_srvs_INCLUDE_DIRS})
#include_directories(${message_generation_INCLUDE_DIRS})
#include_directories(${CMAKE_SOURCE_DIR}/third_party/include)
#include_directories(${CMAKE_SOURCE_DIR}/third_party/include/simple-websocket-server)
#include_directories(${LIBMONGOCXX_STATIC_INCLUDE_DIRS})
#include_directories(${LIBBSONCXX_STATIC_INCLUDE_DIRS})

#include_directories(
#    ${CMAKE_SOURCE_DIR}/core/include
#    ${CMAKE_SOURCE_DIR}/skill/include
#    ${CMAKE_SOURCE_DIR}/task/include
#    ${CMAKE_SOURCE_DIR}/interface/include
#    ${CMAKE_SOURCE_DIR}/manipulation_primitive/include
#    ${CMAKE_SOURCE_DIR}/utils/include
#    ${CMAKE_SOURCE_DIR}/plugins/include
#    ${CMAKE_SOURCE_DIR}/panda/include
#    ${CMAKE_SOURCE_DIR}/controller_pipeline/include
#    ${CMAKE_SOURCE_DIR}/safety/include
#    ${CMAKE_SOURCE_DIR}/memory/include
#    ${CMAKE_SOURCE_DIR}/portal/include
#    ${CMAKE_SOURCE_DIR}/learning_module/include
#    ${CMAKE_SOURCE_DIR}/libraries/include
#    ${CMAKE_SOURCE_DIR}/ros_workspace/devel/include
#    ${CMAKE_SOURCE_DIR}/telemetry/include)

#link_directories(${CMAKE_SOURCE_DIR}/extern/lib)

#set(PLUGINS mogen_p2p mogen_p2p_joint cntr_aic cntr_force cntr_joint_imp cntr_joint_var_imp cntr_mux cntr_nullsp_proj
#    conv_vel2pose motion_error_cart virtual_cube virtual_walls_joint)
#link_directories(${CMAKE_SOURCE_DIR}/lib/plugins)

#set(SOURCES core/src/core.cpp interface/src/interface.cpp manipulation_primitive/src/manipulation_primitive.cpp manipulation_primitive/src/primitive_strategy.cpp
#    skill/src/skill.cpp task/src/task.cpp task/src/task_engine.cpp panda/src/softhand2.cpp panda/src/qbmove_communications.cpp learning_module/src/learning_module.cpp
#    task/src/taskfactory.cpp task/src/taskobserver.cpp skill/src/skill_library.cpp skill/src/skill_engine.cpp portal/src/portal.cpp panda/src/panda_body.cpp interface/src/ros_node.cpp
#    telemetry/src/telemetry_udp.cpp)

#set(UTILS_SRC utils/src/actuator.cpp utils/src/percept.cpp utils/src/object.cpp utils/src/exceptions.cpp utils/src/results.cpp utils/src/event.cpp)

#set(MEMORY_SRC memory/src/memory.cpp memory/src/lt_memory.cpp memory/src/st_memory.cpp memory/src/mongodb_client.cpp memory/src/parameters.cpp)

#set(CONTROLLER_SRC controller_pipeline/src/cart_torque_pipeline.cpp controller_pipeline/src/joint_torque_pipeline.cpp controller_pipeline/src/cart_velocity_pipeline.cpp
#    controller_pipeline/src/joint_velocity_pipeline.cpp controller_pipeline/src/null_pipeline.cpp)

#set(SAFETY_SRC safety/src/velocity_walls.cpp safety/src/virtual_cube.cpp safety/src/virtual_joint_walls.cpp safety/src/cartesian_velocity_damping.cpp)

##set(SOURCES_PRIMITIVES manipulation_primitive/src/primitives/mp_basic.cpp manipulation_primitive/src/primitives/mp_basic_joint.cpp manipulation_primitive/src/primitives/nullprimitive.cpp)

#if(MINIMAL_BUILD)
#    set(SOURCES_SKILLS libraries/src/skills/null_skill.cpp libraries/src/skills/move_to_pose_joint.cpp libraries/src/skills/generic_wiggle_motion.cpp libraries/src/skills/hold_pose.cpp libraries/src/skills/test_skill_1.cpp)
#    set(SOURCES_TASKS libraries/src/tasks/null_task.cpp libraries/src/tasks/idle_task.cpp libraries/src/tasks/test_task_1.cpp libraries/src/tasks/test_task_2.cpp libraries/src/tasks/test_task_3.cpp)
#    set(SOURCES_STRATEGIES libraries/src/strategies/null_strategy.cpp libraries/src/strategies/move_to_joint_pose.cpp libraries/src/strategies/twist_wiggle_strategy.cpp)
#else()
#    file(GLOB SOURCES_SKILLS "libraries/src/skills/*.cpp")
#    file(GLOB SOURCES_TASKS "libraries//src/tasks/*.cpp")
#    file(GLOB SOURCES_STRATEGIES "libraries/src/strategies/*.cpp")
#endif()

#add_executable(mios main/src/mios.cpp ${SOURCES} ${MEMORY_SRC} ${UTILS_SRC} ${CONTROLLER_SRC} ${SAFETY_SRC} ${SOURCES_STRATEGIES} ${SOURCES_SKILLS} ${SOURCES_TASKS} ${SOURCES_PATTERN})

#set_target_properties(mios PROPERTIES UNITY_BUILD ON)
#target_precompile_headers(mios PRIVATE ${CMAKE_SOURCE_DIR}/utils/include/utils/pch.hpp)

#target_link_libraries(mios ${PLUGINS} franka mongocxx-static ${LIBMONGOCXX_STATIC_LIBRARIES} stdc++fs ${roscpp_LIBRARIES} pybind11::embed msrm_cpp_utils ssl crypto pthread boost_system)


#install(TARGETS mios DESTINATION ${CMAKE_SOURCE_DIR}/bin)
