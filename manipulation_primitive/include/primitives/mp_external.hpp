#pragma once

#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <sstream>
#include <deque>
#include <poll.h>
#include <atomic>
#include <thread>

#include "manipulation_primitive/manipulation_primitive.hpp"
#include "plugins/motion_error_cart_wrapper.hpp"


namespace mios {

enum InputMode{Torque,CartesianVelocityTorque,CartesianVelocity,JointVelocityTorque,JointVelocity,CartesianPosition,JointPosition};

struct ConfigMP_mp_external : public ConfigMP{
    ConfigMP_mp_external(){
        mode=InputMode::Torque;
        port_recv=0;
        input_frequency=1000;
        port_dst=0;
        ip_dst="none";
    }

    unsigned port_recv;
    std::string ip_dst;
    unsigned port_dst;
    InputMode mode;
    double input_frequency;

};

struct EvalMP_mp_external : public EvalMP{

};

struct AttractorExternal : public Attractor{
    void reset(){
    }
};

class mp_external : public ManipulationPrimitive{
public:
    mp_external();

    void initialize(const Percept &p_0,const std::shared_ptr<ConfigUser> config);
    CmdMP& step(const Percept& p);
    void terminate();

    bool in_attractor(const Percept &p);
    bool init_attractor(const Percept &p, const std::shared_ptr<ConfigUser> config);
    bool check_attractor();

    void setup_logs(unsigned long long length);
    void write_logs();

private:
    bool initialize_connections();
    bool terminate_connections();
    void msg_in();
    bool msg_out(const std::vector<double> &payload);
    bool unload_msg(const std::vector<double>& payload);

    std::thread _thr_msg_in;

    // Outgoing connection
    int _s_out;
    struct sockaddr_in _si_other_out,_si_me_out;
    unsigned _slen_out;

    // Incoming connection
    int _s_in;
    struct sockaddr_in _si_other_in,_si_me_in;
    unsigned _slen_in;
    unsigned _bufferlength;

    unsigned _n_package;
    unsigned _n_package_last;
    unsigned _cnt_lost_packages;

    std::deque<std::array<double, 7> > _tau_in;
    std::deque<std::array<double, 6> > _dX_d_in;
    std::deque<std::array<double, 7> > _dq_d_in;
    std::deque<std::array<double, 16> > _O_T_EE_d_in;
    std::deque<std::array<double, 7> > _q_d_in;

    std::atomic<bool> _flag_valid_package;
    std::atomic<bool> _flag_connected;
    std::atomic<bool> _flag_sync;
    std::atomic<bool> _flag_run;
    std::atomic<bool> _flag_return_state;

    unsigned _cnt_send;
    unsigned _send_msg_at_n;
};

}
