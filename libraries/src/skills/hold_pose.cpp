#include "skills/hold_pose.hpp"
#include <spdlog/spdlog.h>
#include "strategies/null_strategy.hpp"

namespace mios {

bool SkillParametersHoldPose::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param(parameters,"t_max",t_max)){
        spdlog::error("Missing parameter: t_max");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersHoldPose::get_parameter_list(){
    return {{"t_max",{}}};
}

HoldPose::HoldPose(const std::string &id, Memory *memory, Portal *portal):Skill("HoldPose",{},id,memory,portal,{ControlMode::mCartTorque,ControlMode::mJointTorque}){
}

std::shared_ptr<ManipulationPrimitive> HoldPose::get_initial_mp(const Percept &p_0){
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("hold_pose",p_0);
    mp->create_strategy<NullStrategy>("s_0",1);
    return mp;
}

bool HoldPose::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersHoldPose> c = read_parameters<SkillParametersHoldPose>();
    double t_run=std::chrono::duration_cast<std::chrono::seconds>(p.time-m_memory->get_live_context()->t_skill).count();
    return t_run>c->t_max;
}

bool HoldPose::check_local_ex_conditions(const Percept &p){
    return true;
}

}
