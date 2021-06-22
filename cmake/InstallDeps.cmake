# json
configure_file(${FETCHCONTENT_BASE_DIR}/json-src/include/nlohmann/json.hpp ${CMAKE_SOURCE_DIR}/include/extern/nlohmann/json.hpp)

# simple-websocket-server
configure_file(${FETCHCONTENT_BASE_DIR}/simple-websocket-server-src/asio_compatibility.hpp ${CMAKE_SOURCE_DIR}/include/extern/simple-websocket-server/asio_compatibility.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/simple-websocket-server-src/client_ws.hpp ${CMAKE_SOURCE_DIR}/include/extern/simple-websocket-server/client_ws.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/simple-websocket-server-src/crypto.hpp ${CMAKE_SOURCE_DIR}/include/extern/simple-websocket-server/crypto.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/simple-websocket-server-src/mutex.hpp ${CMAKE_SOURCE_DIR}/include/extern/simple-websocket-server/mutex.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/simple-websocket-server-src/server_ws.hpp ${CMAKE_SOURCE_DIR}/include/extern/simple-websocket-server/server_ws.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/simple-websocket-server-src/status_code.hpp ${CMAKE_SOURCE_DIR}/include/extern/simple-websocket-server/status_code.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/simple-websocket-server-src/utility.hpp ${CMAKE_SOURCE_DIR}/include/extern/simple-websocket-server/utility.hpp)

# httplib
configure_file(${FETCHCONTENT_BASE_DIR}/cpp-httplib-src/httplib.h ${CMAKE_SOURCE_DIR}/include/extern/httplib/httplib.h)

# jsonrpccxx
configure_file(${FETCHCONTENT_BASE_DIR}/jsonrpc-src/include/jsonrpccxx/batchclient.hpp ${CMAKE_SOURCE_DIR}/include/extern/jsonrpccxx/batchclient.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/jsonrpc-src/include/jsonrpccxx/client.hpp ${CMAKE_SOURCE_DIR}/include/extern/jsonrpccxx/client.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/jsonrpc-src/include/jsonrpccxx/common.hpp ${CMAKE_SOURCE_DIR}/include/extern/jsonrpccxx/common.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/jsonrpc-src/include/jsonrpccxx/dispatcher.hpp ${CMAKE_SOURCE_DIR}/include/extern/jsonrpccxx/dispatcher.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/jsonrpc-src/include/jsonrpccxx/iclientconnector.hpp ${CMAKE_SOURCE_DIR}/include/extern/jsonrpccxx/iclientconnector.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/jsonrpc-src/include/jsonrpccxx/server.hpp ${CMAKE_SOURCE_DIR}/include/extern/jsonrpccxx/server.hpp)
configure_file(${FETCHCONTENT_BASE_DIR}/jsonrpc-src/include/jsonrpccxx/typemapper.hpp ${CMAKE_SOURCE_DIR}/include/extern/jsonrpccxx/typemapper.hpp)
