#include "skills/hold_pose.hpp"
#include <spdlog/spdlog.h>

namespace mios {

bool SkillParametersHoldPose::read_parameters(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param(parameters,"t_max",t_max)){
        spdlog::error("Missing parameter: t_max");
    }
    return true;
}

HoldPose::HoldPose(const std::string &id, Memory *memory, const Percept &p):Skill("HoldPose",{},id,memory,p){
}

std::shared_ptr<ManipulationPrimitive> HoldPose::get_initial_mp(const Percept &p_0){
    return create_mp<BasicPrimitive,MPParametersBasic,BasicAttractor>("hold_pose",p_0);
}

bool HoldPose::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersHoldPose> c = get_parameters<SkillParametersHoldPose>();
    double t_run=std::chrono::duration_cast<std::chrono::seconds>(p.time-m_memory->get_live_context()->t_skill).count();
    return t_run>c->t_max;
}

bool HoldPose::check_local_ex_conditions(const Percept &p){
    return true;
}

void HoldPose::evaluate(){
    write_costs(0,std::chrono::duration_cast<std::chrono::seconds>(get_result().p_1.time-get_result().p_0.time).count());
}

}
