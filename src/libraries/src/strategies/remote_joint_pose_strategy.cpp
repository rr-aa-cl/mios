#include "mios/strategies/remote_joint_pose_strategy.hpp"
#include "mios/portal/portal.hpp"
#include <mirmi_cpp_utils/conversion/conversion.hpp>
#include <functional>

namespace mios {

RemoteJointPoseStrategy::RemoteJointPoseStrategy():PrimitiveStrategy({CommandPatternJointPose}),m_receiver(nullptr),m_portal(nullptr){
    m_q_d_in[0]={0,0,0,0,0,0,0};
}

void RemoteJointPoseStrategy::initialize(const Percept &p_0){
    m_q_d_in[0]=mirmi_utils::convert_to_array<double,7,1>(p_0.proprioception.q);
    m_last_valid_q_d=p_0.proprioception.q;
}

void RemoteJointPoseStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    for(unsigned i=0;i<7;i++){
        cmd.q_d(i)=m_q_d_in[0][i];
    }
    if(!cmd.is_valid()){
        cmd.q_d=m_last_valid_q_d;
    }else{
        m_last_valid_q_d=cmd.q_d;
    }
}

void RemoteJointPoseStrategy::terminate([[maybe_unused]] const Percept &p){
    if(m_receiver!=nullptr){
        m_receiver->disconnect();
    }
    if(m_portal!=nullptr){
        m_portal->close_udp_instream(m_stream_name);
    }
}

bool RemoteJointPoseStrategy::finished(){
    return !m_receiver->is_running();
}

bool RemoteJointPoseStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us, unsigned max_lost_packets, bool multicast, const std::optional<std::string> &host, const std::optional<std::string> &multicast_group){
    m_portal=portal;
    m_stream_name=name;
    m_receiver = m_portal->open_udp_instream(m_stream_name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteJointPoseStrategy::read_stream,this,std::placeholders::_1),multicast, host, multicast_group);
    if(m_receiver==nullptr){
        return false;
    }
    return m_receiver->connect();
}

void RemoteJointPoseStrategy::read_stream(std::vector<double>& data){
    spdlog::trace("RemoveJointPoseStrategy::read_stram() received data!");
    if(data.size()==7){
        for(unsigned i=0;i<7;i++){
            m_q_d_in[0][i]=data[i];
        }
    }
}

}
