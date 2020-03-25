#include "tasks/move_until_contact.hpp"
namespace mios{
move_until_contact::move_until_contact():Task("move_until_contact"){
}
move_until_contact::~move_until_contact(){
}
void move_until_contact::initialize_task(){
    this->create_skill(new move_to_contact(),"move");
}
void move_until_contact::execute_task(){
    this->get_skill("move")->set_object("surface",this->surface);
    static_cast<Config_move_to_contact*>(this->get_skill("move")->get_config())->speed(0)=this->speed;
    this->execute_skill("move");
}
const EvalTask& move_until_contact::evaluate_task(){
return this->_eval_task;
}
bool move_until_contact::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"speed",this->speed)){
        cpp_utils::print_error("Missing parameter: speed");
        return false;
    }
    if(!cpp_utils::read_json_param(params,"surface",this->surface)){
        cpp_utils::print_error("Missing parameter: surface");
        return false;
    }
return true;
}
}
