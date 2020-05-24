#include "primitives/nullprimitive.hpp"

namespace mios {

bool NullAttractor::reached(const Percept &p){
    return true;
}

NullPrimitive::NullPrimitive(const std::string &name, const Percept &p_0, std::shared_ptr<MPParameters> parameters, std::shared_ptr<Attractor> attractor, Memory *memory):
    ManipulationPrimitive("NullPrimitive",name,p_0,parameters,attractor,memory){
}

void NullPrimitive::i_initialize(const Percept &p_0){

}

Actuator* NullPrimitive::step(const Percept &p){
    return &m_cmd;
}

void NullPrimitive::i_terminate(){
}


}
