#pragma once

#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sstream>
#include <deque>
#include <poll.h>
#include <atomic>
#include <unistd.h>


namespace mios {

struct ConfigTelemetryUDP{
    ConfigTelemetryUDP(){
        ip_dst="none";
        port_dst=0;
        packagesize=217;
        frequency=200;
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
struct Subscriber{
    unsigned port;
    std::string ip;
    std::string address;
    std::vector<std::string> subscribtions; 
};

class Telemetry_UDP{
public:
    Telemetry_UDP(Core *core);
    ~Telemetry_UDP();

    //bool initialize(ConfigTelemetryUDP config);

    bool add_subscriber(const std::string &addr, const unsigned port, const std::vector<std::string> &subs);
    bool start_sending();
    bool stop_sending();
    
private:
    bool send(const nlohmann::json &msg_data, const std::string &address, const unsigned port);
    void sending_loop();

    Core *m_core;

    std::vector<Subscriber> subscriber_vector;
    //std::map<std::pair<std::string, unsigned>, std::vector<std::string> > m_address_sub_map;
    std::atomic<bool> keep_running;
    std::thread sending_thread;

    unsigned m_frequency;  //ms
    int m_socket;

};

}
