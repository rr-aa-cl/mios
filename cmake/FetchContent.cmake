find_package(Eigen3 REQUIRED)
find_package(pinocchio REQUIRED)

message("################################## ENTERING FETCHCONTENT FILE ##################################")
if(NOT TARGET Eigen3::Eigen3)
  message("Eigen3::Eigen3 TARGET IS NOT SET, add_library, set taget properties to ${EIGEN3_INCLUDE_DIRS} and ${EIGEN§_DEFINITIONS}.")
  add_library(Eigen3::Eigen3 INTERFACE IMPORTED)
  set_target_properties(Eigen3::Eigen3 PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES ${EIGEN3_INCLUDE_DIRS}
    INTERFACE_COMPILE_DEFINITIONS "${EIGEN3_DEFINITIONS}"
  )
endif()

include(FetchContent)
set(FETCHCONTENT_QUIET OFF)
set(FETCHCONTENT_BASE_DIR ${CMAKE_SOURCE_DIR}/_deps)
set(BUILD_EXAMPLES OFF CACHE INTERNAL "No examples")  # needed for libfranka version > 0.15 
set(BUILD_TESTS OFF CACHE INTERNAL "No examples")

FetchContent_Declare(
    libfranka
    #GIT_REPOSITORY https://github.com/frankarobotics/libfranka-release.git
    GIT_REPOSITORY https://github.com/frankarobotics/libfranka.git
    #GIT_TAG upstream/0.9.2)
    GIT_TAG 0.21.1)
    #GIT_REPOSITORY https://github.com/frankaemika/libfranka-release.git
    #GIT_TAG upstream/0.5.0)
    
    #GIT_REPOSITORY https://github.com/frankaemika/libfranka.git
    #GIT_TAG 0.13.6)
# list(APPEND CMAKE_PREFIX_PATH "/opt/openrobots/lib/cmake")  # libfranka >0.15


# --- JSONRPC MANUAL CLONE HACK ---
set(JSONRPC_DIR "${CMAKE_SOURCE_DIR}/_deps/jsonrpc-src")

if(NOT EXISTS "${JSONRPC_DIR}/CMakeLists.txt")
    message(STATUS "Hijacking FetchContent: Manually cloning jsonrpc v0.3.0...")
    execute_process(
        COMMAND git clone -b v0.3.0 https://github.com/jsonrpcx/json-rpc-cxx.git ${JSONRPC_DIR}
        RESULT_VARIABLE clone_result
    )
    if(NOT clone_result EQUAL 0)
        message(FATAL_ERROR "Manual Git clone failed for jsonrpc!")
    endif()
endif()

FetchContent_Declare(
    jsonrpc
    SOURCE_DIR ${JSONRPC_DIR}
)

# 1. Define where we want the source to go
set(MIRMI_UTILS_DIR "${CMAKE_SOURCE_DIR}/_deps/mirmi_cpp_utils-src")

# 2. If it hasn't been cloned yet, do it manually using the command we know works
if(NOT EXISTS "${MIRMI_UTILS_DIR}/CMakeLists.txt")
    message(STATUS "Hijacking FetchContent: Manually cloning mirmi_utils dev_samu branch...")
    execute_process(
        COMMAND git clone -b v1.7.2 https://github.com/SchneiderROS/mirmi_utils ${MIRMI_UTILS_DIR}
        RESULT_VARIABLE clone_result
    )
    if(NOT clone_result EQUAL 0)
        message(FATAL_ERROR "Manual Git clone failed!")
    endif()
endif()

# 3. Tell FetchContent to skip the download step and just use our manually cloned folder
FetchContent_Declare(
    mirmi_cpp_utils
    SOURCE_DIR ${MIRMI_UTILS_DIR}
)



# --- FIX FOR JSONRPC / DOCTEST GLIBC INCOMPATIBILITY ---
# Force doctest to skip the problematic SIGSTKSZ array creation
add_compile_definitions(DOCTEST_CONFIG_NO_POSIX_SIGNALS)

# Aggressively tell dependencies not to build their tests or examples
set(BUILD_TESTING OFF CACHE BOOL "Disable tests" FORCE)
set(BUILD_TESTS OFF CACHE BOOL "Disable tests" FORCE)
set(BUILD_EXAMPLES OFF CACHE BOOL "Disable examples" FORCE)

set(FETCHCONTENT_UPDATES_DISCONNECTED ON CACHE INTERNAL "")

FetchContent_MakeAvailable(libfranka mirmi_cpp_utils)
