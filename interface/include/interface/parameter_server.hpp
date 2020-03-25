#pragma once

#pragma once

#include <string>
#include <deque>
#include <array>
#include <thread>
#include <functional>

#include "cpp_utils/network.hpp"
#include "cpp_utils/output.hpp"

namespace mios {

class ParameterServer{
public:
    ParameterServer();
    ~ParameterServer();

    void initialize(unsigned port);
    void start();
    void stop();

    nlohmann::json get_parameter(const std::string& parameter);

private:
    void bind_methods();

    nlohmann::json set_parameter(const nlohmann::json &parameter);

    std::unique_ptr<cpp_utils::JsonWebsocketServer> _ws_server;
    std::map<std::string,nlohmann::json> _parameters;
    std::mutex _mtx_parameters;
};

}
