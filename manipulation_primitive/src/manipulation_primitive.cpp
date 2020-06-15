#include "manipulation_primitive/manipulation_primitive.hpp"
#include "memory/memory.hpp"
#include <spdlog/spdlog.h>

namespace mios {

ManipulationPrimitive::ManipulationPrimitive(const std::string& name, const Percept &p_0, Memory *memory)
    :m_name(name),m_memory(memory),m_cmd(Actuator(p_0,memory->read_parameters()->control)),m_flag_initialized(false),m_flag_terminated(false){
}

Actuator* ManipulationPrimitive::initialize(const Percept &p_0){
    m_cmd.initialize(p_0,m_memory->read_parameters()->control, m_memory->read_parameters()->frames.O_R_T);
    return initialize(p_0,m_cmd);
}

Actuator* ManipulationPrimitive::initialize(const Percept &p_0, const Actuator& cmd){
    m_cmd=cmd;
    m_memory->get_live_context()->t_mp=std::chrono::high_resolution_clock::now();
    for(auto& s : m_strategies){
        s.second.strategy->initialize(p_0);
        s.second.strategy->get_next_command(s.second.cmd,p_0);
    }
    m_flag_initialized=true;
    m_flag_terminated=false;
    return &m_cmd;
}

Actuator* ManipulationPrimitive::step(const Percept &p){
    for(auto& s : m_strategies){
        s.second.strategy->get_next_command(s.second.cmd,p);
    }
    if(!compose_command(p)){
        spdlog::error("Command composition at primitive layer failed.");
        m_cmd.stop();
    }
    m_cmd.t=std::chrono::duration_cast<std::chrono::seconds>(m_memory->get_live_context()->t_mp-std::chrono::high_resolution_clock::now()).count();
    return &m_cmd;
}

void ManipulationPrimitive::terminate(const Percept &p){
    if(m_flag_initialized && !m_flag_terminated){
        for(auto& s : m_strategies){
            s.second.strategy->terminate(p);
        }
    }
}

bool ManipulationPrimitive::compose_command(const Percept& p){
    m_cmd.set_zero(p);
    if(m_strategies.size()==0){
        return false;
    }
    bool TF_T_EE_d_set=false;
    bool TF_F_d_set=false;
    bool q_d_nullspace_set=false;
    bool q_d_set=false;
    bool tau_d_set=false;

    double weight_check=0;

    for(auto& s : m_strategies){
        if(TF_T_EE_d_set && !m_cmd.TF_T_EE_d.isIdentity()){
            return false;
        }else if(!TF_T_EE_d_set && !m_cmd.TF_T_EE_d.isIdentity()){
            m_cmd.TF_T_EE_d=s.second.cmd.TF_T_EE_d;
            TF_T_EE_d_set=true;
        }
        if(TF_F_d_set && !m_cmd.TF_F_d.isZero()){
            return false;
        }else if(!TF_F_d_set && !m_cmd.TF_F_d.isZero()){
            m_cmd.TF_F_d=s.second.cmd.TF_F_d;
            TF_F_d_set=true;
        }
        if(q_d_nullspace_set && !m_cmd.q_d_nullspace.isZero()){
            return false;
        }else if(!q_d_nullspace_set && !m_cmd.q_d_nullspace.isZero()){
            m_cmd.q_d_nullspace=s.second.cmd.q_d_nullspace;
            q_d_nullspace_set=true;
        }
        if(q_d_set && !m_cmd.q_d.isZero()){
            return false;
        }else if(!q_d_set && !m_cmd.q_d.isZero()){
            m_cmd.q_d=s.second.cmd.q_d;
            q_d_set=true;
        }
        if(tau_d_set && !m_cmd.tau_d.isZero()){
            return false;
        }else if(!tau_d_set && !m_cmd.tau_d.isZero()){
            m_cmd.tau_d=s.second.cmd.tau_d;
            tau_d_set=true;
        }
        m_cmd.TF_dX_d+=s.second.cmd.TF_dX_d*s.second.weight;
        m_cmd.TF_F_ff+=s.second.cmd.TF_F_ff*s.second.weight;
        m_cmd.K_x+=s.second.cmd.K_x*s.second.weight;
        m_cmd.xi_x+=s.second.cmd.xi_x*s.second.weight;

        m_cmd.dq_d+=s.second.cmd.dq_d*s.second.weight;
        m_cmd.tau_ff+=s.second.cmd.tau_ff*s.second.weight;
        m_cmd.K_theta+=s.second.cmd.K_theta*s.second.weight;
        m_cmd.xi_theta+=s.second.cmd.xi_theta*s.second.weight;

        weight_check+=s.second.weight;
    }
    if(weight_check!=1){
        spdlog::error("Strategy command weights do not sum up to 1");
        return false;
    }
    return true;
}

Actuator* ManipulationPrimitive::cmd_from_buffer(){
    m_cmd.read_from_buffer();
    return &m_cmd;
}

Actuator* ManipulationPrimitive::stop(const Percept& p){
    m_cmd.set_zero(p);
    return &m_cmd;
}


bool ManipulationPrimitive::get_flag_error() const{
    return m_flag_error;
}

void ManipulationPrimitive::set_flag_error(){
    m_flag_error=true;
}

std::string ManipulationPrimitive::get_name() const{
    return m_name;
}

bool ManipulationPrimitive::is_settled() const{
    return m_cmd.is_settled(m_memory->read_parameters()->limits);
}

const std::shared_ptr<PrimitiveStrategy> ManipulationPrimitive::get_strategy_interface(const std::string &name) const{
    return m_strategies.at(name).strategy;
}

}
