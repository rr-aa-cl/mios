message(STATUS "--- Loading Project Dependencies ---")
include(FetchContent)
# ==========================================
# 1. System & Pre-built Packages
# ==========================================

find_package(Eigen3 REQUIRED)


# 3. Tell FetchContent to skip the download step and just use our manually cloned folder
FetchContent_Declare(
    mirmi_cpp_utils
    GIT_REPOSITORY https://github.com/SchneiderROS/mirmi_utils
    GIT_TAG v1.7.4
    GIT_SHALLOW FALSE)
# set(FETCHCONTENT_UPDATES_DISCONNECTED ON CACHE INTERNAL "")


# Build the downloaded source
FetchContent_MakeAvailable(mirmi_cpp_utils)

# mirmi_utils v1.7.4 uses std::numeric_limits in its files component without
# including <limits>.  The ROS-only Core build does not inherit the legacy PCH
# that used to hide this upstream omission.  Keep the compatibility include
# confined to that third-party target and to compilers that support -include.
if(TARGET files AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(files PRIVATE -include limits)
endif()
