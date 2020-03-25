#include "tasks/idle_task.hpp"

namespace mios {

idle_task::idle_task():Task("idle_task"){
}
idle_task::~idle_task(){
}
void idle_task::initialize_task(){
    this->create_skill<motions_generic_wiggle>("sleep");
    this->create_skill<hold_pose>("hold");
    this->create_skill<move_to_pose_joint>("move");
}
void idle_task::execute_task(){
    std::map<std::string,std::array<unsigned,3> > colors;
    colors["far-left"]={0,0,100};
    colors["left"]={0,0,100};
    colors["middle"]={0,0,100};
    colors["right"]={0,0,100};
    colors["far-right"]={0,0,100};
    this->load_led_pattern(std::make_shared<pattern_status>());
    switch(cpp_utils::str_to_int(this->idle_mode.c_str())){
    case cpp_utils::str_to_int("none"):
        this->sleep_1ms();
        break;
    case cpp_utils::str_to_int("sleep"):
//        this->get_skill("move")->set_object("loc_goal","pose_sleep");
//        this->execute_skill("move");
        this->execute_skill("sleep");
//        this->get_skill("move")->set_object("loc_goal","pose_attention");
//        this->execute_skill("move");
        this->sleep_1ms();
        break;
    case cpp_utils::str_to_int("hold"):
        this->execute_skill("hold");
        break;
    default:
        cpp_utils::print_warning("Idle mode with id "+this->idle_mode+" does not exist, reverting to default mode.");
        this->sleep_1ms();
        break;
    }
}
void idle_task::recover_task(){

}

bool idle_task::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"idle_mode",this->idle_mode)){
        this->idle_mode="none";
    }
return true;
}

const EvalTask& idle_task::evaluate_task(){
this->_eval_task.cost_suc=0;
this->_eval_task.cost_err=0;
this->_eval_task.success=true;
return this->_eval_task;
}

}
