#include "strategies/remote_torque_strategy.hpp"
#include "portal/portal.hpp"
#include <functional>
#include <math.h>
#include "msrm_cpp_utils/math.hpp"

namespace mios {

RemoteTorqueStrategy::RemoteTorqueStrategy():PrimitiveStrategy({CommandPatternJointFFTorque}),m_receiver(nullptr),m_portal(nullptr){
    m_tau_in[0]={0,0,0,0,0,0,0};
}

void RemoteTorqueStrategy::initialize(const Percept &p_0){
}

void RemoteTorqueStrategy::get_next_command(Actuator &cmd, const Percept &p){
    double power_in;
    double power_scale;
    double p_thr=1;
    for(unsigned i=0;i<7;i++){
        cmd.tau_ff(i)=-m_tau_in[0][i];
        power_in=p.proprioception.dq(i)*m_tau_in[0][i];
//        power_scale=1-0.5*(1-cos(M_PI*(1-power_in/p_thr)));
        if(power_scale>p_thr)power_scale=0;
        if(power_scale<=0)power_scale=1;
        if(power_in<0){
            cmd.tau_ff(i)-=m_alpha(i)*msrm_utils::sgn(p.proprioception.dq(i))*fabs(power_in);
        }
    }
}

void RemoteTorqueStrategy::terminate(const Percept &p){
    if(m_receiver!=nullptr){
        m_receiver->disconnect();
    }
    if(m_portal!=nullptr){
        m_portal->close_udp_instream(m_stream_name);
    }
}

bool RemoteTorqueStrategy::finished(){
    return !m_receiver->is_running();
}

bool RemoteTorqueStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us,unsigned max_lost_packets){
    m_portal=portal;
    m_stream_name=name;
    m_receiver = m_portal->open_udp_instream(m_stream_name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteTorqueStrategy::read_stream,this,std::placeholders::_1),false);
    if(m_receiver==nullptr){
        return false;
    }
    return m_receiver->connect();
}

void RemoteTorqueStrategy::read_stream(std::vector<double>& data){
    if(data.size()==7){
        for(unsigned i=0;i<7;i++){
            m_tau_in[0][i]=data[i];
        }
    }else{
        m_tau_in[0]={0,0,0,0,0,0,0};
    }
}

void RemoteTorqueStrategy::set_damping(Eigen::Matrix<double, 7, 1> alpha){
    m_alpha=alpha;
}

}
