#include "tasks/feature_collision_detection.hpp"

namespace mios {

feature_collision_detection::feature_collision_detection():Task("feature_collision_detection"){
}
void feature_collision_detection::initialize_task(){
    this->create_skill<move_to_pose_joint>("move");
    this->create_skill<move_to_pose_cart>("move_cart");
    this->create_skill<gesture_haptic>("confirm");
}
void feature_collision_detection::execute_task(){
    this->get_skill("move")->set_object("loc_goal",this->pose_init);
    this->execute_skill("move");

    while(!this->get_stop_flag()){
        while(!this->get_skill("move_cart")->get_eval().success && !this->get_stop_flag()){
            this->get_skill("move_cart")->set_object("loc_goal","feature_left");
            this->execute_skill("move_cart");
            if(!this->get_skill("move_cart")->get_eval().success){
                this->execute_skill("confirm");
            }
        }
        this->get_skill("move_cart")->reset();
        while(!this->get_skill("move_cart")->get_eval().success && !this->get_stop_flag()){
            this->get_skill("move_cart")->set_object("loc_goal","feature_right");
            this->execute_skill("move_cart");
            if(!this->get_skill("move_cart")->get_eval().success){
                this->execute_skill("confirm");
            }
        }
        this->get_skill("move_cart")->reset();
    }

}
const EvalTask &feature_collision_detection::evaluate_task(){
this->_eval_task.cost_suc=0;
this->_eval_task.cost_err=0;
this->_eval_task.success=true;
return this->_eval_task;
}

bool feature_collision_detection::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"pose_init",this->pose_init)){
        msrm_utils::print_error("Missing parameter: pose_init");
        return false;
    }
    return true;
}

}
