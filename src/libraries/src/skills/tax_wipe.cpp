#include "mios/skills/tax_wipe.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/strategies/twist_strategy.hpp"
#include "mios/strategies/ff_strategy.hpp"

#include "msrm_cpp_utils/math/math.hpp"

namespace mios{

bool SkillParametersTaxWipe::from_json(const nlohmann::json& parameters){
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

    if(parameters.find("p1")==parameters.end()){
        spdlog::error("Parameters for primitive 1 are missing.");
        return false;
    }else if(parameters.find("p1")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p1"],"K_x",p1.K_x)){
            spdlog::error("Missing parameter: p1.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p1"],"dX_d",p1.dX_d)){
            spdlog::error("Missing parameter: p1.dX_d");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p1"],"ddX_d",p1.ddX_d)){
            spdlog::error("Missing parameter: p1.ddX_d");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p1"],"f_wipe",p1.f_wipe)){
            spdlog::error("Missing parameter: p1.f_wipe");
            return false;
        }
    }

    if(parameters.find("p2")==parameters.end()){
        spdlog::error("Parameters for primitive 2 are missing.");
        return false;
    }else if(parameters.find("p2")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p2"],"K_x",p2.K_x)){
            spdlog::error("Missing parameter: p2.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p2"],"dX_d",p2.dX_d)){
            spdlog::error("Missing parameter: p2.dX_d");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p2"],"ddX_d",p2.ddX_d)){
            spdlog::error("Missing parameter: p2.ddX_d");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p1"],"f_wipe",p1.f_wipe)){
            spdlog::error("Missing parameter: p1.f_wipe");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxWipe::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}},{"p1",{"K_x","dX_d","ddX_d","f_wipe"}},{"p2",{"K_x","dX_d","ddX_d","f_wipe"}}};
}

TaxWipe::TaxWipe(const std::string& name, Memory* memory, Portal* portal):Skill("TaxWipe",{"Approach","Wipeable","Wiper","Direction"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxWipe::get_O_R_T_0(const Percept &p) const{
    return get_object("Wipeable")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxWipe::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxWipe::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            return create_wipe_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxWipe::create_approach_mp(const Percept &p){
    spdlog::trace("TaxWipe::create_approach_mp()");
    std::shared_ptr<SkillParametersTaxWipe> skill_params = get_parameters<SkillParametersTaxWipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a = get_object_pose_T("Approach");
    move->set_goal(T_a,skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxWipe::create_contact_mp(const Percept &p){
    spdlog::trace("TaxWipe::create_contact_mp");
    std::shared_ptr<SkillParametersTaxWipe> skill_params = get_parameters<SkillParametersTaxWipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    Eigen::Matrix<double,3,1> dir=get_object_pose_T("Wipeable").block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3);;
    dir/=dir.norm();
    dX_d<<dir*skill_params->p1.dX_d(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->p1.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxWipe::create_wipe_mp(const Percept &p){
    spdlog::trace("TaxWipe::create_wipe_mp()");
    std::shared_ptr<SkillParametersTaxWipe> skill_params = get_parameters<SkillParametersTaxWipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("wipe",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    mp->create_strategy<FFStrategy>("push",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Direction"),skill_params->p2.dX_d,skill_params->p2.ddX_d);
    std::shared_ptr<FFStrategy> push = mp->get_strategy<FFStrategy>("push");
    Eigen::Matrix<double,6,1> F_d;
    F_d<<0,0,skill_params->p2.f_wipe,0,0,0;
    push->set_TF_F_ff(F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p2.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxWipe::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Wiper")->name){
        return false;
    }
    return true;
}

bool TaxWipe::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Wiper")->name){
        return true;
    }
    if(get_active_mp()->get_name()=="wipe"){
        if(p.proprioception.TF_F_ext_K(2)<m_memory->read_parameters()->user.F_ext_contact(0)){
            return true;
        }
    }
    return false;
}

bool TaxWipe::check_local_suc_conditions(const Percept &p){
    return is_in_env("Direction",p,true);
}

bool TaxWipe::check_local_ex_conditions(const Percept &p){
    return true;
}

}
