#pragma once

#include <array>
#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sstream>
#include <deque>
#include <poll.h>
#include <cstring>
#include <cassert>
#include <atomic>
#include <unistd.h>


namespace mios {

class SimInterface{
public:
    SimInterface();
    ~SimInterface();

    bool connect_to_sim(std::string ip,unsigned port);

    bool send_cmd_torques(std::array<double,7> tau_J_d);
    bool recv_state(std::array<double,200>& state);

private:

    // common parameters

    char _buf[1024];
    std::atomic<bool> _flag_valid;
    std::atomic<bool> _flag_connected;

    // Outgoing connection
    int _s_out;
    struct sockaddr_in _si_other_out,_si_me_out;
    unsigned _slen_out;
    unsigned _n_package;
    unsigned _packagesize_out;

    // Incoming connection
    int _s_in;
    struct sockaddr_in _si_other_in,_si_me_in;
    unsigned _slen_in;
    unsigned _bufferlength;
    unsigned _packagesize_in;
    unsigned _n_package_last;
    unsigned _cnt_lost_packages;
    unsigned _cnt_no_connection;
    bool _lost_package;

};

}
