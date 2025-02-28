find_package(Eigen3 REQUIRED)

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

FetchContent_Declare(
    libfranka
    GIT_REPOSITORY https://github.com/frankaemika/libfranka-release.git
    GIT_TAG upstream/0.9.2)
    #GIT_REPOSITORY https://github.com/frankaemika/libfranka-release.git
    #GIT_TAG upstream/0.5.0)
    
    #GIT_REPOSITORY https://github.com/frankaemika/libfranka.git
    #GIT_TAG 0.13.6)
set(BUILD_EXAMPLES OFF CACHE INTERNAL "No examples")
set(BUILD_TESTS OFF CACHE INTERNAL "No examples")

FetchContent_Declare(
    mirmi_cpp_utils
    GIT_REPOSITORY https://gitlab.lrz.de/mirmi-internal/mirmi_utils.git
    GIT_TAG dev_samu)

set(FETCHCONTENT_UPDATES_DISCONNECTED ON CACHE INTERNAL "")

FetchContent_MakeAvailable(libfranka mirmi_cpp_utils)

