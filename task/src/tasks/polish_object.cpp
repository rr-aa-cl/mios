#include "tasks/polish_object.hpp"

namespace mios {

polish_object::polish_object():Task("polish_object"){
}
polish_object::~polish_object(){
}
void polish_object::initialize_task(){
    this->create_skill(std::shared_ptr<move_to_pose_joint>(new move_to_pose_joint()),"move");
    this->create_skill(std::shared_ptr<move_to_contact>(new move_to_contact()),"contact");
    this->create_skill(std::shared_ptr<polish>(new polish()),"polish");

    this->create_subtask(std::shared_ptr<handover_object>(new handover_object()),"handover");
}
void polish_object::execute_task(){

    if(this->is_grasping()){
        this->grasp_object("polisher");
    }

    this->get_skill("move")->set_object("loc_goal",this->object);
    this->execute_skill("move");
    this->get_skill("contact")->set_object("surface",this->object);
    this->execute_skill("contact");
    this->get_skill("polish")->set_object("surface",this->object);
    this->execute_skill("polish");

}
const EvalTask &polish_object::evaluate_task(){
this->_eval_task.cost_suc=0;
this->_eval_task.cost_err=0;
this->_eval_task.success=true;
return this->_eval_task;
}

bool polish_object::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"object",this->object)){
        cpp_utils::print_error("Missing parameter: object");
        return false;
    }
    return true;
}

}
