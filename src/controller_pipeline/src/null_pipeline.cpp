#include "controller_pipeline/null_pipeline.hpp"

namespace mios {

NullControllerPipeline::NullControllerPipeline():m_panda_cmd({0,0,0,0,0,0,0}){

}

void NullControllerPipeline::initialize(const Percept &p_0, Memory *memory){

}

franka::Finishable* NullControllerPipeline::step(const Percept &p, const Actuator &cmd){
    return &m_panda_cmd;
}

bool NullControllerPipeline::is_valid_command(const franka::Finishable *const cmd) const{
    return false;
}

void NullControllerPipeline::update_percept(Percept::Controller &p){

}

void NullControllerPipeline::terminate(){

}

void NullControllerPipeline::context_switch(const Percept &p){

}

}
