#include "learning_module/learning_module.hpp"
#include "spdlog/spdlog.h"

namespace mios {

LearningModule::LearningModule(){
    pybind11::initialize_interpreter();
    try{
        m_ml_interface=pybind11::module::import("interface.interface").attr("Interface")();
    }catch(const pybind11::error_already_set& e){
        spdlog::debug(e.what());
    }
}

LearningModule::~LearningModule(){
    pybind11::finalize_interpreter();
}

std::string LearningModule::learn_task(const nlohmann::json &problem_definition, const nlohmann::json &service_configuration, const nlohmann::json &agents){
    return "INVALID";
}

bool LearningModule::stop_learning(const std::string &uuid){
    return true;
}

}
