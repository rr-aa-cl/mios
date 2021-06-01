#include "skills/tax_pull.hpp"
#include "strategies/desired_wrench_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include <msrm_cpp_utils/math.hpp>

namespace mios{

bool SkillParametersTaxPull::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"speed",speed)){
        spdlog::error("Parameter speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"acc",acc)){
        spdlog::error("Parameter acc could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxPull::get_parameter_list(){
    return {{"speed",{}},{"acc",{}}};
}

TaxPull::TaxPull(const std::string& name, Memory* memory, Portal *portal):Skill("TaxPull",{"Pullable","GoalLocation"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxPull::get_O_R_T_0(const Percept &p) const{
    if(get_object("Pullable")->name!="NullObject"){
        return get_object("Pullable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxPull::get_initial_mp(const Percept& p){
    return create_pull_mp(p);
}

std::shared_ptr<ManipulationPrimitive> TaxPull::create_pull_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxPull> skill_params = get_parameters<SkillParametersTaxPull>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("pull",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("GoalLocation"),skill_params->speed,skill_params->acc);
    return mp;
}

bool TaxPull::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Pullable")->name){
        return false;
    }
    return true;
}

bool TaxPull::check_local_suc_conditions(const Percept &p){
    return get_active_mp()->get_strategy_interface("move")->finished();
}

bool TaxPull::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Pullable")->name){
        return true;
    }
    return false;
}

}
