#include "skills/tax_carry.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/cart_compliance_strategy.hpp"
#include <franka/exception.h>

namespace mios {

bool SkillParametersTaxCarry::from_json(const nlohmann::json &parameters){
    if(parameters.find("p0")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p0")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p0"],"K_x",p0.K_x)){
            spdlog::error("Missing parameter: p0.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p0"],"dX_d",p0.dX_d)){
            spdlog::error("Missing parameter: p0.dX_d");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p0"],"ddX_d",p0.ddX_d)){
            spdlog::error("Missing parameter: p0.ddX_d");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxCarry::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}}};
}

TaxCarry::TaxCarry(const std::string &id, Memory *memory, Portal *portal):Skill("TaxCarry",{"Carriable","GoalPose"},id,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}),
m_finished(false){
}

std::shared_ptr<ManipulationPrimitive> TaxCarry::get_initial_mp(const Percept &p_0){
    return create_move_mp(p_0);
}

std::shared_ptr<ManipulationPrimitive> TaxCarry::create_move_mp(const Percept &p){
    spdlog::trace("TaxCarry::create_move_mp");
    std::shared_ptr<SkillParametersTaxCarry> skill_params = get_parameters<SkillParametersTaxCarry>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("GoalPose"),skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxCarry::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Carriable")->name){
        return false;
    }
    return true;
}

bool TaxCarry::check_local_suc_conditions(const Percept &p){
    if(is_in_env("GoalPose","move",p)){
        return true;
    }else{
        return false;
    }
}

bool TaxCarry::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Carriable")->name){
        return true;
    }
    return false;
}

}
