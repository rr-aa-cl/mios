include(FetchContent)
set(FETCHCONTENT_QUIET OFF)
set(FETCHCONTENT_BASE_DIR ${PROJECT_SOURCE_DIR}/_deps)

FetchContent_Declare(
    jsonrpc
    GIT_REPOSITORY https://github.com/jsonrpcx/json-rpc-cxx.git
    GIT_TAG v0.3.0)

set(COMPILE_TESTS OFF CACHE INTERNAL "Build SHARED libraries")
set(COMPILE_EXAMPLES OFF CACHE INTERNAL "Build SHARED libraries")

FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/ArthurSonzogni/nlohmann_json_cmake_fetchcontent.git
    GIT_TAG v3.9.1)

FetchContent_Declare(
    simple-websocket-server
    GIT_REPOSITORY https://gitlab.com/eidheim/Simple-WebSocket-Server.git
    GIT_TAG v2.0.2)

FetchContent_Declare(
    cpp-httplib
    GIT_REPOSITORY https://github.com/yhirose/cpp-httplib.git
    GIT_TAG v0.8.9)

FetchContent_MakeAvailable(jsonrpc json simple-websocket-server cpp-httplib)

