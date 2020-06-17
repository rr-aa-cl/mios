#include "strategies/remote_torque_strategy.hpp"
#include "portal/portal.hpp"
#include <functional>

namespace mios {

void RemoteTorqueStrategy::initialize(const Percept &p_0){
}

void RemoteTorqueStrategy::get_next_command(Actuator &cmd, const Percept &p){
    for(unsigned i=0;i<7;i++){
        cmd.tau_ff(i)=-m_tau_in[0][i];
    }
}

void RemoteTorqueStrategy::terminate(const Percept &p){

}

bool RemoteTorqueStrategy::finished(){
    return !m_receiver->is_running();
}

bool RemoteTorqueStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us,unsigned max_lost_packets){
    m_receiver = portal->open_udp_instream(name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteTorqueStrategy::read_stream,this,std::placeholders::_1));
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

}
