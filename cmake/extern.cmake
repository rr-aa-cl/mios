FetchContent_Declare(
    msrm_utils
    GIT_REPOSITORY https://gitlab.lrz.de/ge29miq/msrm_utils.git
    GIT_TAG v1.2.0)
set(BUILD_TESTS OFF CACHE INTERNAL "No tests")

FetchContent_Declare(
    libfranka
    GIT_REPOSITORY https://github.com/frankaemika/libfranka-release.git
    GIT_TAG upstream/0.8.0)
set(BUILD_EXAMPLES OFF CACHE INTERNAL "No examples")

FetchContent_MakeAvailable(msrm_utils libfranka)

