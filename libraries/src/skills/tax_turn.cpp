#include "skills/tax_turn.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/cart_compliance_strategy.hpp"

namespace mios{
bool SkillParametersTaxTurn::from_json(const nlohmann::json& parameters){
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

std::map<std::string, std::set<std::string> > SkillParametersTaxTurn::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}}};
}

TaxTurn::TaxTurn(const std::string& id, Memory* memory, Portal* portal):Skill("Turn",{"Turnable","GoalOrientation"},id,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){

}

Eigen::Matrix<double,3,3> TaxTurn::get_O_R_T_0(const Percept &p) const{
    if(get_object("Turnable")->name!="NullObject"){
        return get_object("Turnable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxTurn::get_initial_mp(const Percept& p){
    return create_turn_mp(p);
}

std::shared_ptr<ManipulationPrimitive> TaxTurn::create_turn_mp(const Percept &p){
    spdlog::trace("TaxTurn::create_turn_mp");
    std::shared_ptr<SkillParametersTaxTurn> skill_params = get_parameters<SkillParametersTaxTurn>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("turn",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("GoalOrientation"),skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxTurn::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Turnable")->name){
        return false;
    }
    return true;
}

bool TaxTurn::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Turnable")->name){
        return true;
    }
    return false;
}

bool TaxTurn::check_local_suc_conditions(const Percept &p){
    if(get_active_mp()->get_strategy_interface("move")->finished()){
        if((p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("GoalOrientation").block<3,1>(0,3)).norm()<m_memory->read_parameters()->user.env_X(0)
           && acos(((get_object_pose_T("GoalOrientation").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2) < m_memory->read_parameters()->user.env_X(1)){
            return true;
        }else{
            return false;
        }
    }
    return false;
}

double TaxTurn::get_goal_heuristic(const Percept &p){
    return acos(((get_object_pose_T("GoalOrientation").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2);
}

}
