#include "mios/strategies/remote_cart_pose_strategy.hpp"
#include "mios/portal/portal.hpp"
#include <msrm_cpp_utils/conversion/conversion.hpp>
#include <functional>

namespace mios {

RemoteCartPoseStrategy::RemoteCartPoseStrategy():PrimitiveStrategy({CommandPatternCartesianPose}),m_receiver(nullptr),m_portal(nullptr){
    m_O_T_EE_d_in[0]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
}

void RemoteCartPoseStrategy::initialize(const Percept &p_0){
    m_O_T_EE_d_in[0]=msrm_utils::convert_to_array<double,4,4>(p_0.proprioception.T_T_EE);
}

void RemoteCartPoseStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    for(unsigned i=0;i<4;i++){
        for(unsigned j=0;j<4;j++){
            cmd.TF_T_EE_d(j,i)=m_O_T_EE_d_in[0][4*i+j];
        }
    }
}

void RemoteCartPoseStrategy::terminate([[maybe_unused]] const Percept &p){
    if(m_receiver!=nullptr){
        m_receiver->disconnect();
    }
    if(m_portal!=nullptr){
        m_portal->close_udp_instream(m_stream_name);
    }
}

bool RemoteCartPoseStrategy::finished(){
    return !m_receiver->is_running();
}

bool RemoteCartPoseStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us,unsigned max_lost_packets, bool multicast){
    m_portal=portal;
    m_stream_name=name;
    m_receiver = m_portal->open_udp_instream(m_stream_name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteCartPoseStrategy::read_stream,this,std::placeholders::_1),multicast);
    if(m_receiver==nullptr){
        return false;
    }
    return m_receiver->connect();
}

void RemoteCartPoseStrategy::read_stream(std::vector<double>& data){
    if(data.size()==16){
        for(unsigned i=0;i<16;i++){
            m_O_T_EE_d_in[0][i]=data[i];
        }
    }
}

}
