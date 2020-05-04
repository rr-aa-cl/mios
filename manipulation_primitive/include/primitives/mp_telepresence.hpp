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
#include "motion_error_cart/motion_error_cart_wrapper.hpp"
//#include "wave_variables/wave_variables_wrapper.hpp"


namespace mios {

enum TelepresenceMode{None,JointDirect,CartesianDirect,Joystick};

struct ConfigMP_mp_telepresence : public ConfigMP{
    ConfigMP_mp_telepresence(){
        ip_dst="none";
        port_dst=0;
        port_recv=0;
        master=false;
        repeater=false;
        bilateral=true;
        EE_T_J_t=Eigen::Matrix<double,3,3>::Identity();
        EE_T_J_r=Eigen::Matrix<double,3,3>::Identity();
        K_joystick_on.setZero();
        K_joystick_off.setZero();
        joystick_deadband.setZero();
        joystick_amp<<1,1,1,1,1,1;
        joystick_lever.setZero();
        joystick_f_ext_amp.setZero();
        joystick_force_input=false;
        joystick_funnel_pose.setIdentity();

        joint_direct_alpha.setZero();
        joystick_stepwise=false;
        joystick_step_size.setZero();
    }

    Eigen::Matrix<double,3,3> EE_T_J_t;
    Eigen::Matrix<double,3,3> EE_T_J_r;

    Eigen::Matrix<double,6,1> K_joystick_on;
    Eigen::Matrix<double,6,1> K_joystick_off;
    Eigen::Matrix<double,6,1> joystick_deadband;
    bool joystick_force_input;
    Eigen::Matrix<double,6,1> joystick_amp;
    Eigen::Matrix<double,3,1> joystick_lever;
    Eigen::Matrix<double,6,1> joystick_f_ext_amp;
    Eigen::Matrix<double,4,4> joystick_funnel_pose;

    bool joystick_stepwise;
    Eigen::Matrix<double,2,1> joystick_step_size;

    Eigen::Matrix<double,7,1> joint_direct_alpha;


    std::string ip_dst;
    unsigned port_dst;
    unsigned port_recv;
    bool master;
    bool repeater;
    bool bilateral;
    TelepresenceMode mode;

};

struct EvalMP_mp_telepresence : public EvalMP{

};

struct AttractorTelepresence : public Attractor{
    void reset(){
    }
};

class mp_telepresence : public ManipulationPrimitive{
public:
    mp_telepresence();

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
    bool msg_out(const std::vector<double>& payload);
    bool unload_msg(const std::vector<double>& payload);
    void write_safe_message();
    void joint_direct_mode(const Percept& p, std::vector<double>& payload);
    void cartesian_direct_mode(const Percept& p, std::vector<double>& payload);
    void joystick_mode(const Percept& p, std::vector<double>& payload);

    std::thread _thr_msg_in;

    // Outgoing connection
    int _s_out;
    struct sockaddr_in _si_other_out,_si_me_out;
    unsigned _slen_out;

    // Repeater connection
    int _s_rep;
    struct sockaddr_in _si_other_rep,_si_me_rep;
    unsigned _slen_rep;

    // Incoming connection
    int _s_in;
    struct sockaddr_in _si_other_in,_si_me_in;
    unsigned _slen_in;
    unsigned _bufferlength;

    unsigned _n_package;
    unsigned _n_package_last;
    unsigned _cnt_lost_packages;

    std::deque<std::array<double, 7> > _q_d_in;
    std::deque<std::array<double, 7> > _dq_d_in;
    std::deque<std::array<double, 7> > _tau_ext_in;

    std::deque<std::array<double, 16> > _O_T_EE_in;
    std::deque<std::array<double, 6> > _O_dX_d_in;
    std::deque<std::array<double, 6> > _EE_F_ext_in;

    std::atomic<bool> _flag_valid_package;
    std::atomic<bool> _flag_connected;
    std::atomic<bool> _thread_should_run;

    bool _flag_joystick_translation;
    bool _flag_joystick_rotation;
    Eigen::Matrix<bool,6,1> _joystick_selector;

    unsigned _cnt_send;
    Eigen::Matrix<double,6,1> _joystick_dX_max;

    Eigen::Matrix<double,6,1> _rot_limits;

    Eigen::Matrix<double,4,4> _TF_T_EE_0;
    Eigen::Matrix<double,3,1> _J_phi;
    Eigen::Matrix<double,6,1> _J_dX_step;

    motion_error_cart::motion_error_cart _motion_error;
    motion_error_cart::In_U_motion_error_cart _motion_error_u;
    motion_error_cart::Out_Y_motion_error_cart _motion_error_y;

    motion_error_cart::motion_error_cart _motion_error_0;
    motion_error_cart::In_U_motion_error_cart _motion_error_0_u;
    motion_error_cart::Out_Y_motion_error_cart _motion_error_0_y;

//    wave_variables::wave_variables _wave_variables;

};

}
