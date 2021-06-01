#include "skills/tax_bend.hpp"
#include "strategies/desired_wrench_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include <msrm_cpp_utils/math.hpp>

namespace mios{

bool SkillParametersTaxBend::from_json(const nlohmann::json& parameters){
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

std::map<std::string, std::set<std::string> > SkillParametersTaxBend::get_parameter_list(){
    return {{"speed",{}},{"acc",{}}};
}

TaxBend::TaxBend(const std::string& name, Memory* memory, Portal *portal):Skill("TaxBend",{"Bendable", "GoalPosition"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxBend::get_O_R_T_0(const Percept &p) const{
    if(get_object("Bendable")->name!="NullObject"){
        return get_object("Bendable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxBend::get_initial_mp(const Percept& p){
    return create_bend_mp(p);
}

std::shared_ptr<ManipulationPrimitive> TaxBend::create_bend_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxBend> skill_params = get_parameters<SkillParametersTaxBend>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("bend",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("GoalPosition"),skill_params->speed,skill_params->acc);
    return mp;
}

bool TaxBend::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Bendable")->name){
        return false;
    }
    return true;
}

bool TaxBend::check_local_suc_conditions(const Percept &p){
    return get_active_mp()->get_strategy_interface("move")->finished();
}

bool TaxBend::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Bendable")->name){
        return true;
    }
    return false;
}

}
