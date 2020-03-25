#include "tasks/feature_force_control.hpp"

namespace mios {

feature_force_control::feature_force_control():Task("feature_force_control"){
}
void feature_force_control::initialize_task(){
    this->create_skill<move_to_pose_joint>("move");
    this->create_skill<move_to_contact>("contact");
    this->create_skill<push>("push");

//    this->create_subtask(new handover_object(),"handover");
}
void feature_force_control::execute_task(){

    this->get_skill("move")->set_object("loc_goal",this->pose_init);
    this->execute_skill("move");

    this->get_skill("move")->set_object("loc_goal","scale");
    this->execute_skill("move");
    this->execute_skill("contact");
    if(!this->get_skill("contact")->get_eval().success){
        cpp_utils::print_error("Contact skill failed, can not risk force control without established contact.");
    }else{
        this->execute_skill("push");
    }

    this->get_skill("move")->set_object("loc_goal","scale");
    this->execute_skill("move");
    this->get_skill("move")->set_object("loc_goal","feature_default");
    this->execute_skill("move");

}

void feature_force_control::recover_task(){
    this->get_skill("move")->set_object("loc_goal","feature_default");
    this->execute_skill("move");
}

const EvalTask &feature_force_control::evaluate_task(){
this->_eval_task.cost_suc=0;
this->_eval_task.cost_err=0;
this->_eval_task.success=true;
return this->_eval_task;
}

bool feature_force_control::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"pose_init",this->pose_init)){
        cpp_utils::print_error("Missing parameter: pose_init");
        return false;
    }
    return true;
}

}
