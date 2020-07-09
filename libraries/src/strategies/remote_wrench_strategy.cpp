#include "strategies/remote_wrench_strategy.hpp"
#include "portal/portal.hpp"
#include <functional>

namespace mios {

RemoteWrenchStrategy::RemoteWrenchStrategy():PrimitiveStrategy({CommandPatternCartesianFFWrench}){

}

void RemoteWrenchStrategy::initialize(const Percept &p_0){
}

void RemoteWrenchStrategy::get_next_command(Actuator &cmd, const Percept &p){
    for(unsigned i=0;i<6;i++){
        cmd.TF_F_ff(i)=m_TF_F_ff_in[0][i];
    }
}

void RemoteWrenchStrategy::terminate(const Percept &p){

}

bool RemoteWrenchStrategy::finished(){
    return !m_receiver->is_running();
}

bool RemoteWrenchStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us,unsigned max_lost_packets){
    m_receiver = portal->open_udp_instream(name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteWrenchStrategy::read_stream,this,std::placeholders::_1));
    if(m_receiver==nullptr){
        return false;
    }
    return m_receiver->connect();
}

void RemoteWrenchStrategy::read_stream(std::vector<double>& data){
    if(data.size()==6){
        for(unsigned i=0;i<6;i++){
            m_TF_F_ff_in[0][i]=data[i];
        }
    }else{
        m_TF_F_ff_in[0]={0,0,0,0,0,0};
    }
}

}
