#include "tasks/idle_task.hpp"
#include "skills/motions_generic_wiggle.hpp"
#include "skills/hold_pose.hpp"
#include "skills/move_to_pose_joint.hpp"
#include "patterns/pattern_status.hpp"

namespace mios {

IdleTask::IdleTask(Core *core):Task("IdleTask",core){
}
void IdleTask::initialize_task(){
    this->create_skill<motions_generic_wiggle>("sleep",m_kb,std::make_shared<SkillParameters_motions_generic_wiggle>());
    this->create_skill<hold_pose>("hold",m_kb,std::make_shared<SkillParameters_hold_pose>());
    this->create_skill<move_to_pose_joint>("move",m_kb,std::make_shared<SkillParameters_move_to_pose_joint>());
}
void IdleTask::execute_task(){
    std::map<std::string,std::array<unsigned,3> > colors;
    colors["far-left"]={0,0,100};
    colors["left"]={0,0,100};
    colors["middle"]={0,0,100};
    colors["right"]={0,0,100};
    colors["far-right"]={0,0,100};
    this->load_led_pattern(std::make_shared<pattern_status>());
    switch(msrm_utils::str_to_int(this->idle_mode.c_str())){
    case msrm_utils::str_to_int("none"):
        this->sleep_1ms();
        break;
    case msrm_utils::str_to_int("sleep"):
//        this->get_skill("move")->set_object("loc_goal","pose_sleep");
//        this->execute_skill("move");
        this->execute_skill("sleep");
//        this->get_skill("move")->set_object("loc_goal","pose_attention");
//        this->execute_skill("move");
        this->sleep_1ms();
        break;
    case msrm_utils::str_to_int("hold"):
        this->execute_skill("hold");
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

const EvalTask& IdleTask::evaluate_task(){
m_eval_task.cost_suc=0;
m_eval_task.cost_err=0;
m_eval_task.success=true;
return m_eval_task;
}

}
