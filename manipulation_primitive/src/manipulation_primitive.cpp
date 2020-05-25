#include "manipulation_primitive/manipulation_primitive.hpp"
#include "memory/memory.hpp"

namespace mios {

ManipulationPrimitive::ManipulationPrimitive(const std::string &type, const std::string& name, const Percept &p_0, std::shared_ptr<MPParameters> parameters, std::shared_ptr<Attractor> attractor, Memory *memory)
    :m_memory(memory),m_cmd(Actuator(p_0)),m_flag_initialized(false),m_flag_terminated(false),m_parameters(parameters),m_attractor(attractor),m_type(type),m_name(name){
}

ManipulationPrimitive::~ManipulationPrimitive(){
    terminate();
}

Actuator* ManipulationPrimitive::initialize(const Percept &p_0){
    m_cmd.initialize(p_0);
    m_memory->get_live_context()->t_mp=std::chrono::high_resolution_clock::now();
    i_initialize(p_0);
    m_flag_initialized=true;
    m_flag_terminated=false;
    return &m_cmd;
}

Actuator* ManipulationPrimitive::initialize(const Percept &p_0, const Actuator& cmd){
    m_cmd=cmd;
    i_initialize(p_0);
    m_flag_initialized=true;
    m_flag_terminated=false;
    return &m_cmd;
}

void ManipulationPrimitive::terminate(){
    if(m_flag_initialized && !m_flag_terminated){
        i_terminate();
    }
}

Actuator* ManipulationPrimitive::cmd_from_buffer(){
    m_cmd.read_from_buffer();
    return &m_cmd;
}

Actuator* ManipulationPrimitive::stop(const Percept& p){
    m_cmd.initialize(p);
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

std::string ManipulationPrimitive::get_type() const{
    return m_type;
}

bool ManipulationPrimitive::is_settled() const{
    return m_cmd.is_settled(m_memory->read_parameters()->limits);
}

}
