#include "tasks/move_to_location.hpp"
namespace mios{
move_to_location::move_to_location():Task("move_to_location"){
}
void move_to_location::initialize_task(){
    this->create_skill<move_to_pose_cart>("move_cart");
    this->create_skill<move_to_pose_joint>("move_joint");
}
void move_to_location::execute_task(){

    this->get_skill("move_cart")->get_config()->general.control_mode=0;
    this->get_skill("move_joint")->get_config()->general.control_mode=0;
    for(unsigned i=0;i<this->loc_intermediate.size();i++){
        if(this->loc_cart[i]==1){
            this->get_skill("move_cart")->set_object("loc_goal",this->loc_intermediate[i]);
            this->execute_skill("move_cart");
        }else{
            this->get_skill("move_joint")->set_object("loc_goal",this->loc_intermediate[i]);
            this->execute_skill("move_joint");
        }
    }
    if(this->loc_cart[this->loc_intermediate.size()]==1){
        this->get_skill("move_cart")->set_object("loc_goal",this->loc_goal);
        this->execute_skill("move_cart");
    }else{
        this->get_skill("move_joint")->set_object("loc_goal",this->loc_goal);
        this->execute_skill("move_joint");
    }

}
const EvalTask& move_to_location::evaluate_task(){
    return this->_eval_task;
}
bool move_to_location::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"loc_goal",this->loc_goal)){
        msrm_utils::print_error("Missing parameters: loc_goal");
        return false;
    }
    if(!msrm_utils::read_json_param<std::string>(params,"loc_intermediate",this->loc_intermediate)){
        this->loc_intermediate.resize(0);
    }
    if(!msrm_utils::read_json_param<int>(params,"loc_cart",this->loc_cart)){
        this->loc_cart.resize(0);
    }
    if(this->loc_cart.size()!=this->loc_intermediate.size()+1){
        msrm_utils::print_error("Size of loc_cart must be the size of loc_intermediate plus one.");
        return false;
    }

    return true;
}
}
