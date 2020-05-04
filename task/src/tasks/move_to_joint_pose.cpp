#include "tasks/move_to_joint_pose.hpp"

namespace mios {

move_to_joint_pose::move_to_joint_pose():Task("move_to_joint_pose"){
}
void move_to_joint_pose::initialize_task(){
    this->create_skill<move_to_pose_joint>("move");
}
void move_to_joint_pose::execute_task(){
    this->load_led_pattern(std::shared_ptr<pattern_white>(new pattern_white()));
    this->get_skill("move")->set_object("loc_goal",this->pose);
    if(this->pose=="none"){
        std::static_pointer_cast<ConfigSkill_move_to_pose_joint>(this->get_skill("move")->get_config())->q_g=this->q_g;
    }
    std::static_pointer_cast<ConfigSkill_move_to_pose_joint>(this->get_skill("move")->get_config())->speed(0)=this->speed;
    std::static_pointer_cast<ConfigSkill_move_to_pose_joint>(this->get_skill("move")->get_config())->acc(0)=this->acc;
    this->execute_skill("move");
}
const EvalTask &move_to_joint_pose::evaluate_task(){
this->_eval_task.cost_suc=0;
this->_eval_task.cost_err=0;
this->_eval_task.success=true;
return this->_eval_task;
}

bool move_to_joint_pose::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"pose",this->pose)){
        this->pose="none";
    }
    if(!msrm_utils::read_json_param<double,7,1>(params,"q_g",this->q_g) && this->pose=="none"){
        msrm_utils::print_error("Missing parameters: pose or q_g");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"speed",this->speed)){
        this->speed=0.5;
    }
    if(!msrm_utils::read_json_param(params,"acc",this->acc)){
        this->acc=0.5;
    }
    return true;
}

}
