#pragma once
#include <string>
#include <iostream>

namespace mios{

struct MiosConfiguration {
    std::string verbosity;
    std::string robot_ip;
    std::string database_name;

    unsigned    robot_configuration;
    unsigned    database_port;
    unsigned    websocket_port;
    unsigned    udp_port;
    unsigned    rpc_port;
    bool        use_desk;
    // Define how this struct should be printed
    friend std::ostream& operator<<(std::ostream& os, const MiosConfiguration& c) {
        os << "MiosConfiguration: {\n"
           << "  verbosity:           " << c.verbosity << "\n"
           << "  robot_ip:            " << c.robot_ip << "\n"
           << "  robot_configuration: " << c.robot_configuration << "\n"
           << "  use_desk:            " << c.use_desk << "\n"
           << "  database_name:       " << c.database_name << "\n"
           << "  database_port:       " << c.database_port << "\n"
           << "  websocket_port:      " << c.websocket_port << "\n"
           << "  rpc_port:            " << c.rpc_port << "\n"
           << "  udp_port:            " << c.udp_port << "\n";
        return os;
    }
};

}