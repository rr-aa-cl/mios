#include "tasks/push_button.hpp"
namespace mios{
push_button::push_button():Task("push_button"){
}
push_button::~push_button(){
}
void push_button::initialize_task(){
    this->create_subtask(new move_to_cart_pose(),"move_to_button");
    this->create_skill(new move_to_contact(),"contact");
    this->create_skill(new button_pushing(),"push");
}
void push_button::execute_task(){
    nlohmann::json parameters;
    parameters["pose"]=this->button;

    if(!this->get_subtask("move_to_button")->read_parameters(parameters)){
        return;
    }
    this->execute_subtask("move_to_button");
    if(!this->get_subtask("move_to_button")->get_eval().success){
        cpp_utils::print_error("Could not approach button.");
        return;
    }

    if(this->contact){
        this->get_skill("contact")->set_object("surface",this->button);
        this->execute_skill("contact");
        if(!this->get_skill("contact")->get_eval().success){
            cpp_utils::print_error("Could not establish contact, aborting push button task");
            return;
        }
    }

    this->get_skill("push")->set_object("button",this->button);
    this->execute_skill("push");

}
const EvalTask& push_button::evaluate_task(){
    this->_eval_task.success=this->get_skill("push")->get_eval().success;
    return this->_eval_task;
}
bool push_button::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"button",this->button)){
        cpp_utils::print_error("Missing parameter: button");
        return false;
    }
    if(!cpp_utils::read_json_param(params,"contact",this->contact)){
        this->contact=false;
    }
    return true;
}
}
