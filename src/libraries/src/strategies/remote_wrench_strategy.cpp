#include "mios/strategies/remote_wrench_strategy.hpp"
#include "mios/portal/portal.hpp"
#include "mirmi_cpp_utils/math/math.hpp"
#include <functional>

namespace mios {

RemoteWrenchStrategy::RemoteWrenchStrategy():PrimitiveStrategy({CommandPatternCartesianFFWrench}),m_receiver(nullptr),m_portal(nullptr){
    m_TF_F_ff_in[0]={0,0,0,0,0,0};
}

void RemoteWrenchStrategy::initialize(const Percept &p_0){
}

void RemoteWrenchStrategy::get_next_command(Actuator &cmd, const Percept &p){
    double power_in;
    double power_scale;
    double p_thr=1;
    for(unsigned i=0;i<6;i++){
        cmd.TF_F_ff(i)=-m_TF_F_ff_in[0][i];
        power_in=p.proprioception.TF_dX_EE(i)*m_TF_F_ff_in[0][i];
        power_scale=1-0.5*(1-cos(M_PI*(1-power_in/p_thr)));
        if(power_scale>p_thr)power_scale=0;
        if(power_scale<=0)power_scale=1;
        if(power_in<0){
            cmd.TF_F_ff(i)-=m_alpha(i)*mirmi_utils::sgn(p.proprioception.TF_dX_EE(i))*fabs(power_in);
        }
    }
    //cmd.TF_F_ff(3)=0;
    //cmd.TF_F_ff(4)=0;
    //cmd.TF_F_ff(5)=0;
    if(!cmd.is_valid()){
        cmd.TF_F_ff.setZero();
    }
}

void RemoteWrenchStrategy::terminate(const Percept &p){
    if(m_receiver!=nullptr){
        m_receiver->disconnect();
    }
    if(m_portal!=nullptr){
        m_portal->close_udp_instream(m_stream_name);
    }
}

bool RemoteWrenchStrategy::finished(){
    return !m_receiver->is_running();
}

void RemoteWrenchStrategy::set_damping(Eigen::Matrix<double, 6, 1> alpha){
    m_alpha=alpha;
}

bool RemoteWrenchStrategy::connect(Portal *portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us,unsigned max_lost_packets, bool multicast, const std::optional<std::string> &host, const std::optional<std::string> &multicast_group){
    m_portal=portal;
    m_stream_name=name;
    m_receiver = m_portal->open_udp_instream(m_stream_name,port,buffer_size,timeout_s,timeout_us,max_lost_packets,std::bind(&RemoteWrenchStrategy::read_stream,this,std::placeholders::_1),multicast,host, multicast_group);
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
