#include "tasks/idle_task.hpp"
#include "skills/generic_wiggle_motion.hpp"
#include "skills/hold_pose.hpp"
#include "skills/move_to_pose_joint.hpp"

#include <msrm_utils/files.hpp>
#include <spdlog/spdlog.h>

namespace mios {

IdleTask::IdleTask(Core *core):Task("IdleTask",core){
}
void IdleTask::initialize_context(){
    reserve_skill("sleep");
    reserve_skill("hold");
    reserve_skill("move");
}
void IdleTask::execute(){
    switch(msrm_utils::str_to_int(this->idle_mode.c_str())){
    case msrm_utils::str_to_int("none"):
        this->sleep_1ms();
        break;
    case msrm_utils::str_to_int("sleep"):
//        this->get_skill("move")->set_object("loc_goal","pose_sleep");
//        this->execute_skill("move");
        execute_skill<GenericWiggleMotion,SkillParametersGenericWiggleMotion>("sleep");
        this->sleep_1ms();
        break;
    case msrm_utils::str_to_int("hold"):
        execute_skill<HoldPose,SkillParametersHoldPose>("hold");
        break;
    default:
        spdlog::warn("Idle mode with id "+this->idle_mode+" does not exist, reverting to default mode.");
        this->sleep_1ms();
        break;
    }
}
void IdleTask::recover_task(){

}

bool IdleTask::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"idle_mode",idle_mode)){
        idle_mode="none";
    }
return true;
}

void IdleTask::get_default_context(nlohmann::json &context){
    context["parameters"] = nlohmann::json();
    context["parameters"]["idle_mode"]="none";

    context["skills"]=nlohmann::json();
    context["skills"]["hold"]=nlohmann::json();
    context["skills"]["hold"]["control"]={{"control_mode",0}};
    context["skills"]["hold"]["type"]="HoldPose";
    context["skills"]["move"]=nlohmann::json();
    context["skills"]["move"]["control"]={{"control_mode",3}};
    context["skills"]["move"]["type"]="MoveToPoseJoint";
    context["skills"]["sleep"]=nlohmann::json();
    context["skills"]["sleep"]["control"]={{"control_mode",2}};
    context["skills"]["sleep"]["type"]="GenericWiggleMotion";
}

}
