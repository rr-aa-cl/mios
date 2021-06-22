#include "mios/controller_pipeline/null_pipeline.hpp"
#include "spdlog/spdlog.h"

namespace mios {

NullControllerPipeline::NullControllerPipeline():m_panda_cmd({0,0,0,0,0,0,0}){
    spdlog::trace("NullControllerPipeline::NullControllerPipeline");
}

void NullControllerPipeline::initialize([[maybe_unused]] const Percept &p_0, [[maybe_unused]] Memory *memory){
    spdlog::trace("NullControllerPipeline::initialize");
}

franka::Finishable* NullControllerPipeline::step([[maybe_unused]] const Percept &p, [[maybe_unused]] const Actuator &cmd){
    return &m_panda_cmd;
}

bool NullControllerPipeline::is_valid_command([[maybe_unused]] const franka::Finishable *const cmd) const{
    return false;
}

void NullControllerPipeline::update_percept([[maybe_unused]] Percept::Controller &p){

}

void NullControllerPipeline::terminate(){
    spdlog::trace("NullControllerPipeline::terminate");
}

void NullControllerPipeline::context_switch(const Percept &p){
    spdlog::trace("NullControllerPipeline::context_switch");
}

}
