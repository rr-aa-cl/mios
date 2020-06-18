#include "strategies/remote_joint_pose_strategy.hpp"
#include "portal/portal.hpp"
#include <functional>
#include <msrm_utils/conversion.hpp>

namespace mios {

RemoteJointPoseStrategy::RemoteJointPoseStrategy():PrimitiveStrategy(false,false,true){

}

void RemoteJointPoseStrategy::initialize(const Percept &p_0){
    m_q_d_in[0]=msrm_utils::convert_to_array<double,7,1>(p_0.proprioception.q);
}

void RemoteJointPoseStrategy::get_next_command(Actuator &cmd, const Percept &p){
    for(unsigned i=0;i<7;i++){
        cmd.q_d(i)=m_q_d_in[0][i];
    }
}

void RemoteJointPoseStrategy::terminate(const Percept &p){
    m_receiver->disconnect();
}

bool RemoteJointPoseStrategy::finished(){
    return !m_receiver->is_running();
}

bool RemoteJointPoseStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us,unsigned max_lost_packets){
    m_receiver = portal->open_udp_instream(name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteJointPoseStrategy::read_stream,this,std::placeholders::_1));
    if(m_receiver==nullptr){
        return false;
    }
    return m_receiver->connect();
}

void RemoteJointPoseStrategy::read_stream(std::vector<double>& data){
    if(data.size()==7){
        for(unsigned i=0;i<7;i++){
            m_q_d_in[0][i]=data[i];
        }
    }
}

}
