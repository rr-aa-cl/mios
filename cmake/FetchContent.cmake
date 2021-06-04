include(FetchContent)
set(FETCHCONTENT_QUIET OFF)
set(FETCHCONTENT_BASE_DIR ${PROJECT_SOURCE_DIR}/_deps)

FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/ArthurSonzogni/nlohmann_json_cmake_fetchcontent.git
    GIT_TAG v3.9.1)

FetchContent_Declare(
    libfranka
    GIT_REPOSITORY https://github.com/frankaemika/libfranka-release.git
    GIT_TAG upstream/0.8.0)
set(BUILD_EXAMPLES OFF CACHE INTERNAL "No examples")
set(BUILD_TESTS OFF CACHE INTERNAL "No examples")

FetchContent_MakeAvailable(json libfranka)

