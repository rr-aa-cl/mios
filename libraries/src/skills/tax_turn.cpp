#include "skills/tax_turn.hpp"
#include "strategies/move_to_pose.hpp"

namespace mios{
bool SkillParametersTaxTurn::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"turn_speed",turn_speed)){
        spdlog::error("Parameter turn_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"turn_acc",turn_acc)){
        spdlog::error("Parameter turn_acc could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxTurn::get_parameter_list(){
    return {{"turn_speed",{}},{"turn_acc",{}}};
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
    std::shared_ptr<SkillParametersTaxTurn> skill_params = get_parameters<SkillParametersTaxTurn>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("turn",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("GoalOrientation"),skill_params->turn_speed,skill_params->turn_acc);
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
