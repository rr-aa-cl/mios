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
    spdlog::debug("LearningModule::learn_task()");
    try{
        pybind11::dict limits;
        for(const auto& p : problem_definition["domain"]["limits"].items()){
            double lb,ub;
            p.value()[0].get_to(lb);
            p.value()[0].get_to(ub);
            limits[p.key().c_str()]=pybind11::make_tuple(lb,ub);
        }
        pybind11::dict context_mapping;
        for(const auto& p : problem_definition["domain"]["context_mapping"].items()){
            pybind11::list tmp_mappings;
            for(const auto& m : p.value()){
                tmp_mappings.append(m);
            }
            context_mapping[p.key().c_str()]=tmp_mappings;
        }
        pybind11::object domain = pybind11::module::import("problem_definition.domain").attr("Domain")(limits, context_mapping);

        pybind11::dict default_context;
        default_context["name"]="LearnerTest";

        pybind11::object configuration;
        if(service_configuration["service_name"]=="cmaes"){
            configuration = pybind11::module::import("services.cmaes").attr("CMAESConfiguration")();
        }else if(service_configuration["service_name"]=="generic"){
            configuration = pybind11::module::import("services.generic_optimizer").attr("GenericOptimizerConfiguration")();
        }
        pybind11::object problem_definition = pybind11::module::import("problem_definition.problem_definition").attr("ProblemDefinition")(domain,default_context,pybind11::list(),pybind11::list(),pybind11::list());
        pybind11::set agents_set;
        for(const auto& a : agents){
            std::string agent;
            a.get_to(agent);
            agents_set.add(agent);
        }
        spdlog::debug("LearningModule::learn_task.start_learning");
        pybind11::object result = m_ml_interface.attr("start_learning")(problem_definition, configuration,agents);
        return result.cast<std::string>();
    }catch(const pybind11::error_already_set& e){
        spdlog::debug(e.what());
    }
    return "INVALID";
}

bool LearningModule::stop_learning(const std::string &uuid){
    pybind11::object result = m_ml_interface.attr("start_learning")(uuid);
    return result.cast<bool>();
}

}
