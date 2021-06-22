#include "mios/strategies/remote_twist_strategy.hpp"
#include "mios/portal/portal.hpp"
#include <functional>

namespace mios {

RemoteTwistStrategy::RemoteTwistStrategy():PrimitiveStrategy({CommandPatternCartesianTwist}),m_receiver(nullptr),m_portal(nullptr){
    m_TF_dX_d_in[0]={0,0,0,0,0,0};
    m_static_frame=true;
}

void RemoteTwistStrategy::initialize([[maybe_unused]] const Percept &p_0){
}

void RemoteTwistStrategy::get_next_command(Actuator &cmd, const Percept &p){
    for(unsigned i=0;i<6;i++){
        cmd.TF_dX_d(i)=m_TF_dX_d_in[0][i];
    }
    if(!m_static_frame){
        cmd.TF_dX_d<<p.controller.O_R_T.transpose()*p.proprioception.O_T_EE.block<3,3>(0,0)*cmd.TF_dX_d.block<3,1>(0,0),p.controller.O_R_T.transpose()*p.proprioception.O_T_EE.block<3,3>(0,0)*cmd.TF_dX_d.block<3,1>(3,0);
    }
}

void RemoteTwistStrategy::terminate([[maybe_unused]] const Percept &p){
    if(m_receiver!=nullptr){
        m_receiver->disconnect();
    }
    if(m_portal!=nullptr){
        m_portal->close_udp_instream(m_stream_name);
    }
}

bool RemoteTwistStrategy::finished(){
    return !m_receiver->is_running();
}

bool RemoteTwistStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us, unsigned max_lost_packets, bool multicast){
    m_portal=portal;
    m_stream_name=name;
    m_receiver = m_portal->open_udp_instream(m_stream_name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteTwistStrategy::read_stream,this,std::placeholders::_1),multicast);
    if(m_receiver==nullptr){
        return false;
    }
    return m_receiver->connect();
}

void RemoteTwistStrategy::set_frame(bool static_frame){
    m_static_frame=static_frame;
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
