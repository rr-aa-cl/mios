#include "tasks/idle_task.hpp"
#include "skills/motions_generic_wiggle.hpp"
#include "skills/hold_pose.hpp"
#include "skills/move_to_pose_joint.hpp"

#include <msrm_utils/files.hpp>

namespace mios {

IdleTask::IdleTask(Core *core):Task("IdleTask",core){
}
void IdleTask::initialize_context(){
    reserve_skill("sleep");
    reserve_skill("hold");
    reserve_skill("move");
}
void IdleTask::execute_task(){
    switch(msrm_utils::str_to_int(this->idle_mode.c_str())){
    case msrm_utils::str_to_int("none"):
        this->sleep_1ms();
        break;
    case msrm_utils::str_to_int("sleep"):
//        this->get_skill("move")->set_object("loc_goal","pose_sleep");
//        this->execute_skill("move");
        execute_skill<motions_generic_wiggle>("sleep");
        this->sleep_1ms();
        break;
    case msrm_utils::str_to_int("hold"):
        execute_skill<hold_pose>("hold");
        break;
    default:
        msrm_utils::print_warning("Idle mode with id "+this->idle_mode+" does not exist, reverting to default mode.");
        this->sleep_1ms();
        break;
    }
}
void IdleTask::recover_task(){

}

bool IdleTask::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"idle_mode",this->idle_mode)){
        this->idle_mode="none";
    }
return true;
}

void IdleTask::evaluate_task(){
    write_result(true,0,0,{});
}

}
