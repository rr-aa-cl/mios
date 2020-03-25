#include "tasks/move_trajectory.hpp"
namespace mios{
move_trajectory::move_trajectory():Task("move_trajectory"){
}
move_trajectory::~move_trajectory(){
}
void move_trajectory::initialize_task(){
    this->create_skill(new follow_trajectory(),"move");
}
void move_trajectory::execute_task(){
    static_cast<ConfigSkill_follow_trajectory*>(this->get_skill("move")->get_config())->locations=this->locations;
    static_cast<ConfigSkill_follow_trajectory*>(this->get_skill("move")->get_config())->speed=this->speed;
    static_cast<ConfigSkill_follow_trajectory*>(this->get_skill("move")->get_config())->acc=this->acc;
    static_cast<ConfigSkill_follow_trajectory*>(this->get_skill("move")->get_config())->flag_cart=this->flag_cart;
    this->execute_skill("move");
}
const EvalTask& move_trajectory::evaluate_task(){
    this->_eval_task.success=this->get_skill("move")->get_eval().success;
return this->_eval_task;
}
bool move_trajectory::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param<std::string>(params,"locations",this->locations)){
        this->locations.resize(0);
    }
    if(!cpp_utils::read_json_param<double,2,1>(params,"speed",this->speed)){
        this->speed<<0.1,0.5;
    }
    if(!cpp_utils::read_json_param<double,2,1>(params,"acc",this->acc)){
        this->acc<<0.5,1;
    }
    if(!cpp_utils::read_json_param(params,"flag_cart",this->flag_cart)){
        this->flag_cart=true;
    }
    if(this->locations.size()==0){
        cpp_utils::print_error("No locations given.");
        return false;
    }
return true;
}
}
