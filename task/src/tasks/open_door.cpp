#include "tasks/open_door.hpp"

namespace mios {

open_door::open_door():Task("open_door"){
}
open_door::~open_door(){
}
void open_door::initialize_task(){

    this->create_skill(new push(),"push_key");
    this->create_skill(new turn(),"turn_key");
    this->create_skill(new move_to_pose(),"turn_back");
    this->create_skill(new move_cart_relative(),"move_back");

    this->create_subtask(new move_to_joint_pose(),"move");
    this->create_subtask(new handover_object(),"handover_key");
    this->create_subtask(new insert_object(),"insert_key");
}
void open_door::execute_task(){

    Json::Value p_move;
    p_move["pose"]="pose_handover";
    this->get_subtask("move")->read_parameters(p_move);
    this->execute_subtask("move");

    Json::Value parameters;
    parameters["object"]=this->key;
    this->get_subtask("handover_key")->read_parameters(parameters);
    this->execute_subtask("handover_key");
    if(!this->get_subtask("handover_key")->evaluate_task().success){
        cpp_utils::print_error("Could not grasp the key.");
        return;
    }
    Json::Value p_move2;
    p_move2["pose"]="pose_safe";
    this->get_subtask("move")->read_parameters(p_move2);
    this->execute_subtask("move");

    Json::Value request_insert;
    Json::Value parameters_insert;
    Json::Value skills;
    Json::Value insertion;
    Json::Value skill;
    skill["wiggle_a_t"].append(2);
    skill["wiggle_a_r"].append(2);
    skill["wiggle_f_t"].append(2);
    skill["wiggle_f_r"].append(2);
    skill["time_max"]=4;
    insertion["skill"]=skill;
    skills["insertion"]=insertion;
    parameters_insert["object"]=this->key;
    parameters_insert["hole"]=this->lock;
    parameters_insert["joint"]=false;
    parameters_insert["extract"]=false;
    request_insert["parameters"]=parameters_insert;
    request_insert["skills"]=skills;

    while(!this->get_subtask("insert_key")->get_eval().success && !this->get_stop_flag()){
//        this->execute_subtask("insert_key",request_insert);
    }
    if(this->get_subtask("insert_key")->get_eval().success){
        this->get_skill("turn_back")->set_object("loc_goal",this->lock);
        this->execute_skill("turn_back");
    }

    while(!this->get_skill("turn_key")->get_eval().success && !this->get_stop_flag()){
        this->execute_skill("push_key");
        this->execute_skill("turn_key");
        if(!this->get_skill("turn_key")->get_eval().success){
            this->get_skill("turn_back")->set_object("loc_goal",this->lock);
            this->execute_skill("turn_back");
        }
    }
    this->release_object();
    static_cast<Config_move_cart_relative*>(this->get_skill("move_back")->get_config())->acc=0.3;
    static_cast<Config_move_cart_relative*>(this->get_skill("move_back")->get_config())->speed=0.3;
    static_cast<Config_move_cart_relative*>(this->get_skill("move_back")->get_config())->DX<<0,0,-0.05,0,0,0;
    this->execute_subtask("move");
    p_move2["pose"]="feature_default";
    this->get_subtask("move")->read_parameters(p_move2);
    this->execute_subtask("move");
//    this->execute_skill("move_back");

}
const EvalTask &open_door::evaluate_task(){
    this->_eval_task.cost_suc=0;
    this->_eval_task.cost_err=0;
    this->_eval_task.success=true;
    return this->_eval_task;
}

bool open_door::read_parameters(const Json::Value& params){
    if(!cpp_utils::read_json_param(params["key"],this->key)){
        cpp_utils::print_error("Missing parameter: key");
        return false;
    }
    if(!cpp_utils::read_json_param(params["lock"],this->lock)){
        cpp_utils::print_error("Missing parameter: lock");
        return false;
    }
    return true;
}

}
