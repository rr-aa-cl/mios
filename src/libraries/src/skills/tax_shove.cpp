#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/skills/tax_shove.hpp"
#include "mios/strategies/twist_strategy.hpp"
#include "mios/strategies/move_to_pose.hpp"

#include "msrm_cpp_utils/math/math.hpp"


namespace mios{
bool SkillParametersTaxShove::from_json(const nlohmann::json& parameters){
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
    }
    if(parameters.find("p2")==parameters.end()){
        spdlog::error("Parameters for primitive 2 are missing.");
        return false;
    }else if(parameters.find("p1")!=parameters.end()){
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
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxShove::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}},{"p1",{"K_x","dX_d","ddX_d"}},{"p2",{"K_x","dX_d","ddX_d"}}};
}

TaxShove::TaxShove(const std::string& name, Memory* memory, Portal* portal):Skill("TaxShove",{"Shovable","Approach","Direction"},name,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){
    m_has_contact=true;
}

Eigen::Matrix<double,3,3> TaxShove::get_O_R_T_0(const Percept &p) const{
    return get_object("Shovable")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxShove::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxShove::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            return create_shove_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxShove::create_approach_mp(const Percept &p){
    spdlog::trace("TaxShove::create_approach_mp");
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a = get_object_pose_T("Approach");
    move->set_goal(T_a,skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxShove::create_contact_mp(const Percept &p){
    spdlog::trace("TaxShove::create_contact_mp");
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    Eigen::Matrix<double,3,1> dir=get_object_pose_T("Shovable").block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3);;
    dir/=dir.norm();
    dX_d<<dir*skill_params->p1.dX_d(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->p1.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxShove::create_shove_mp(const Percept &p){
    spdlog::trace("TaxShove::create_shove_mp");
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("shove",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Direction"),skill_params->p2.dX_d,skill_params->p2.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p2.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxShove::check_local_pre_conditions(const Percept &p){
    return true;
}

bool TaxShove::check_local_err_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    if(get_active_mp()->get_name()=="shove" && get_active_mp()->get_strategy_interface("move")->finished()){
        if(!m_has_contact){
            return true;
        }
    }
    return false;
}

bool TaxShove::check_local_suc_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="shove" && get_active_mp()->get_strategy_interface("move")->finished()){
        return true;
    }
    return false;
}

}
