#include "tasks/move_to_cart_pose.hpp"
namespace mios{
move_to_cart_pose::move_to_cart_pose():Task("move_to_cart_pose"){
}
void move_to_cart_pose::initialize_task(){
    this->create_skill<move_to_pose_cart>("move");
}
void move_to_cart_pose::execute_task(){
    this->load_led_pattern(std::shared_ptr<pattern_white>(new pattern_white()));
    this->get_skill("move")->set_object("loc_goal",this->pose);
    if(this->pose=="none"){
        std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("move")->get_config())->TF_T_EE_g=this->TF_T_EE_g;
    }
    std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("move")->get_config())->speed(0)=this->speed;
    std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("move")->get_config())->acc(0)=this->acc;
    this->execute_skill("move");
}
const EvalTask& move_to_cart_pose::evaluate_task(){
    this->_eval_task.cost_suc=0;
    this->_eval_task.cost_err=0;
    this->_eval_task.success=true;
    return this->_eval_task;
}
bool move_to_cart_pose::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"pose",this->pose)){
        this->pose="none";
    }
    if(!cpp_utils::read_json_param<double,4,4>(params,"TF_T_EE_g",this->TF_T_EE_g) && this->pose=="none"){
        cpp_utils::print_error("Missing parameters: pose or TF_T_EE_g");
        return false;
    }
    if(!cpp_utils::read_json_param(params,"speed",this->speed)){
        this->speed=0.5;
    }
    if(!cpp_utils::read_json_param(params,"acc",this->acc)){
        this->acc=0.5;
    }
    return true;
}
}
