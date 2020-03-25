#pragma once

#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sstream>
#include <deque>
#include <poll.h>
#include <atomic>
#include <unistd.h>

#include "knowledge_base/local_memory.hpp"


namespace mios {

struct ConfigTelemetryUDP{
    ConfigTelemetryUDP(){
        ip_dst="none";
        port_dst=0;
        packagesize=217;
        frequency=1000;
        name="none";
        location="none";
    }
    std::string ip_dst;
    unsigned port_dst;
    unsigned packagesize;

    std::string name;
    std::string location;

    unsigned frequency;
};

class Telemetry_UDP{
public:
    Telemetry_UDP();
    ~Telemetry_UDP();

    bool initialize(ConfigTelemetryUDP config);
    bool send_telemetry(const Percept& p);
    bool terminate();

private:

    ConfigTelemetryUDP _config;

    // Outgoing connection
    int _s_out;
    struct sockaddr_in _si_other_out,_si_me_out;
    unsigned _slen_out;
    unsigned _n_package;

    unsigned _cnt_frequency;

};

}
