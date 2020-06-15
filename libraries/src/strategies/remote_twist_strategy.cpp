#include "strategies/remote_twist_strategy.hpp"
#include "portal/portal.hpp"
#include <functional>

namespace mios {

void RemoteTwistStrategy::initialize(const Percept &p_0){
}

void RemoteTwistStrategy::get_next_command(Actuator &cmd, const Percept &p){
    for(unsigned i=0;i<6;i++){
        cmd.TF_dX_d(i)=m_TF_dX_d_in[0][i];
    }
}

void RemoteTwistStrategy::terminate(const Percept &p){

}

bool RemoteTwistStrategy::finished(){
    return false;
}

bool RemoteTwistStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us,unsigned max_lost_packets){
    m_receiver = portal->open_udp_instream(name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteTwistStrategy::read_stream,this,std::placeholders::_1));
    if(m_receiver==nullptr){
        return false;
    }
    return m_receiver->connect();
}

void RemoteTwistStrategy::read_stream(std::vector<double>& data){
    if(data.size()==6){
        for(unsigned i=0;i<6;i++){
            m_TF_dX_d_in[0][i]=data[i];
        }
    }else{
        m_TF_dX_d_in[0]={0,0,0,0,0,0};
    }
}

}
