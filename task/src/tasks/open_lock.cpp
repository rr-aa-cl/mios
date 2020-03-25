#include "tasks/open_lock.hpp"

#include "tasks/insert_object.hpp"

namespace mios{
open_lock::open_lock():Task("open_lock"){
}
open_lock::~open_lock(){
}
void open_lock::initialize_task(){
    this->create_subtask(new insert_object(),"insert_object");
    this->create_skill(new turn(),"turn");
    this->create_skill(new extraction(),"extract");
    this->create_skill(new move_to_pose(),"turn_back");
    this->create_skill(new move_to_pose(),"realign");
}
void open_lock::execute_task(){

    this->get_skill("extract")->set_object("object",this->key);
    this->get_skill("extract")->set_object("hole",this->lock);

    nlohmann::json p;
    p["object"]=this->key;
    p["hole"]=this->lock;

    this->get_subtask("insert_object")->read_parameters(p);
    this->execute_subtask("insert_object");

    if(!this->get_subtask("insert_object")->get_eval().success){
        cpp_utils::print_warning("I will not continue since the key insertion has failed.");
        return;
    }
    Object o;
    this->_kb->load_object(this->lock,o);
    static_cast<Config_move_to_pose*>(this->get_skill("realign")->get_config())->TF_T_EE_g=this->_kb->transform_to_EE(o.TF_T_o(this->get_skill("realign")->get_config()->frames.O_R_TF));
    static_cast<Config_move_to_pose*>(this->get_skill("realign")->get_config())->TF_T_EE_g.block<3,1>(0,3)=this->request_percept(this->get_skill("realign")->get_config()->frames.O_R_TF).TF_T_EE.block<3,1>(0,3);
    this->execute_skill("realign");

    static_cast<ConfigSkill_turn*>(this->get_skill("turn")->get_config())->angle(0)=this->angle;
    this->execute_skill("turn");
    if(this->release){
        this->release_object();
        return;
    }
    if(this->reverse){
        this->get_skill("turn_back")->set_object("loc_goal",this->lock);
        this->execute_skill("turn_back");
        if(this->get_skill("turn_back")->get_eval().success){
            this->execute_skill("extract");
        }
    }

}
const EvalTask& open_lock::evaluate_task(){
    this->_eval_task.success=this->get_skill("turn")->get_eval().success;
    return this->_eval_task;
}
bool open_lock::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"reverse",this->reverse)){
        this->reverse=true;
    }
    if(!cpp_utils::read_json_param(params,"release",this->release)){
        this->release=true;
    }
    if(!cpp_utils::read_json_param(params,"key",this->key)){
        cpp_utils::print_error("Missing parameter: key");
        return false;
    }
    if(!cpp_utils::read_json_param(params,"lock",this->lock)){
        cpp_utils::print_error("Missing parameter: lock");
        return false;
    }
    if(!cpp_utils::read_json_param(params,"angle",this->angle)){
        cpp_utils::print_error("Missing parameter: angle");
        return false;
    }
return true;
}
}
