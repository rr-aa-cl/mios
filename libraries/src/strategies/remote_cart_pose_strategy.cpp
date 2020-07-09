#include "strategies/remote_cart_pose_strategy.hpp"
#include "portal/portal.hpp"
#include <functional>
#include <msrm_utils/conversion.hpp>

namespace mios {

RemoteCartPoseStrategy::RemoteCartPoseStrategy():PrimitiveStrategy({CommandPatternCartesianPose}){

}

void RemoteCartPoseStrategy::initialize(const Percept &p_0){
    m_O_T_EE_d_in[0]=msrm_utils::convert_to_array<double,4,4>(p_0.proprioception.TF_T_EE);
}

void RemoteCartPoseStrategy::get_next_command(Actuator &cmd, const Percept &p){
    for(unsigned i=0;i<4;i++){
        for(unsigned j=0;j<4;j++){
            cmd.TF_T_EE_d(j,i)=m_O_T_EE_d_in[0][4*i+j];
        }
    }
}

void RemoteCartPoseStrategy::terminate(const Percept &p){
    m_receiver->disconnect();
}

bool RemoteCartPoseStrategy::finished(){
    return !m_receiver->is_running();
}

bool RemoteCartPoseStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us,unsigned max_lost_packets){
    m_receiver = portal->open_udp_instream(name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteCartPoseStrategy::read_stream,this,std::placeholders::_1));
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
