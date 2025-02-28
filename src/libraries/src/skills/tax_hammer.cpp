#include "mios/strategies/twist_strategy.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/skills/tax_hammer.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mios/strategies/ff_wiggle_strategy.hpp"

namespace mios {

bool SkillParametersTaxHammer::from_json(const nlohmann::json &parameters){
    if(parameters.find("p0")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p0")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p0"],"K_x",p0.K_x)){
            spdlog::error("Missing parameter: p0.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p0"],"dX_d",p0.dX_d)){
            spdlog::error("Missing parameter: p0.dX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p0"],"ddX_d",p0.ddX_d)){
            spdlog::error("Missing parameter: p0.ddX_d");
            return false;
        }
    }
    if(parameters.find("p1")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p1")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p1"],"K_x",p1.K_x)){
            spdlog::error("Missing parameter: p1.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param(parameters["p1"],"f_hammer",p1.f_hammer)){
            spdlog::error("Missing parameter: p1.f_hammer");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p1"],"dX_d",p1.dX_d)){
            spdlog::error("Missing parameter: p1.dX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p1"],"ddX_d",p1.ddX_d)){
            spdlog::error("Missing parameter: p1.ddX_d");
            return false;
        }
    }
    if(parameters.find("p2")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p2")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p2"],"K_x",p2.K_x)){
            spdlog::error("Missing parameter: p2.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p2"],"dX_d",p2.dX_d)){
            spdlog::error("Missing parameter: p2.dX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p2"],"ddX_d",p2.ddX_d)){
            spdlog::error("Missing parameter: p2.ddX_d");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxHammer::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}},{"p1",{"K_x","f_hammer","dX_d","ddX_d"}},{"p2",{"K_x","dX_d","ddX_d"}}};
}

TaxHammer::TaxHammer(const std::string &name, Memory *memory, Portal* portal):Skill("TaxHammer",{"Approach","Hammerable","Hammer","GoalPosition"},name,memory,portal,
{ControlMode::mCartTorque}){

}


Eigen::Matrix<double, 3, 3> TaxHammer::get_O_R_T_0(const Percept &p) const{
    return get_object("Hammerable")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxHammer::get_initial_mp(const Percept &p_0){
    return create_approach_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxHammer::graph_transition(const Percept &p){
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_down_mp(p);
        }
        else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="down"){
        if(p.proprioception.TF_F_ext_K(2)>skill_params->p1.f_hammer){
            return create_up_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="up"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_down_mp(p);
        }
        else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxHammer::create_approach_mp(const Percept &p){
    spdlog::trace("TaxHammer::create_approach_mp");
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a = get_object_pose_T("Approach");
    move->set_goal(T_a,skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxHammer::create_down_mp(const Percept &p){
    spdlog::trace("TaxHammer::create_down_mp");
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("down",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    dX_d<<0,0,skill_params->p1.dX_d(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->p1.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxHammer::create_up_mp(const Percept &p){
    spdlog::trace("TaxHammer::create_up_mp");
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("up",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->p2.dX_d,skill_params->p2.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p2.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxHammer::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Hammer")->name){
        return false;
    }
    return true;
}

bool TaxHammer::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    if(is_in_env("GoalPosition",p,true)){
        return true;
    }
    return false;
}

bool TaxHammer::check_local_ex_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="up" && get_result().success){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return true;
        }
    }
    return false;
}

bool TaxHammer::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Hammer")->name){
        return true;
    }
    return false;
}

}
