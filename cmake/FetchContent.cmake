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
    GIT_TAG 0.17.0)
    #GIT_REPOSITORY https://github.com/frankaemika/libfranka-release.git
    #GIT_TAG upstream/0.5.0)
    
    #GIT_REPOSITORY https://github.com/frankaemika/libfranka.git
    #GIT_TAG 0.13.6)
# list(APPEND CMAKE_PREFIX_PATH "/opt/openrobots/lib/cmake")  # libfranka >0.15

FetchContent_Declare(
    mirmi_cpp_utils
    GIT_REPOSITORY https://github.com/SchneiderROS/mirmi_utils
    GIT_TAG v1.7.2)

set(FETCHCONTENT_UPDATES_DISCONNECTED ON CACHE INTERNAL "")

FetchContent_MakeAvailable(libfranka mirmi_cpp_utils)
