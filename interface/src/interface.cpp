#include "interface/interface.hpp"

#include "event_publisher/event_publisher.hpp"
#include <msrm_utils/network.hpp>
#include "core/core.hpp"
#include "task/task_handler.hpp"
namespace mios {

Interface::Interface(){
    this->_core=nullptr;
    this->_task_handler=nullptr;
    this->_ws_server=nullptr;
}

Interface::~Interface(){

}

void Interface::initialize(std::shared_ptr<Core> core, std::shared_ptr<TaskHandler> task_handler, unsigned port){
    this->_core=core;
    this->_task_handler=task_handler;

    this->_ws_server = std::make_shared<msrm_utils::JsonWebsocketServer>("0.0.0.0",port,"mios/core");

    this->bind_methods();
}

void Interface::start(){
    msrm_utils::print_info("Starting core interface at endpoint mios/core...",false);
    this->_ws_server->start_listening();
    msrm_utils::print_info("done.");
}

void Interface::stop(){
    msrm_utils::print_info("Stopping core interface...",false);
    this->_ws_server->stop_listening();
    msrm_utils::print_info("done.");
}

void Interface::bind_methods(){
    this->_ws_server->bind_method("start_task",std::bind(&Interface::start_task,this,std::placeholders::_1),{"task","parameters","queue"});
    this->_ws_server->bind_method("stop_task",std::bind(&Interface::stop_task,this,std::placeholders::_1),{"nominal","success","recover","empty_queue","cost_suc","cost_err"});
    this->_ws_server->bind_method("remove_task",std::bind(&Interface::remove_task,this,std::placeholders::_1),{"task_uuid"});
    this->_ws_server->bind_method("wait_for_task",std::bind(&Interface::wait_for_task,this,std::placeholders::_1),{"task_uuid"});
    this->_ws_server->bind_method("check_if_task_finished",std::bind(&Interface::check_if_task_finished,this,std::placeholders::_1),{"task_uuid"});
    this->_ws_server->bind_method("is_busy",std::bind(&Interface::is_busy,this,std::placeholders::_1),{});
    this->_ws_server->bind_method("subscribe_to_event_stream",std::bind(&Interface::subscribe_to_event_stream,this,std::placeholders::_1),{"address","port"});
    this->_ws_server->bind_method("unsubscribe_from_event_stream",std::bind(&Interface::unsubscribe_from_event_stream,this,std::placeholders::_1),{"address","port"});

    this->_ws_server->bind_method("set_grasped_object",std::bind(&Interface::set_grasped_object,this,std::placeholders::_1),{"object"});
    this->_ws_server->bind_method("grasp_object",std::bind(&Interface::grasp_object,this,std::placeholders::_1),{"object","width","speed","force","check_width"});
    this->_ws_server->bind_method("grasp",std::bind(&Interface::grasp,this,std::placeholders::_1),{"width","speed","force"});
    this->_ws_server->bind_method("release_object",std::bind(&Interface::release_object,this,std::placeholders::_1),{"width","speed"});
    this->_ws_server->bind_method("move_gripper",std::bind(&Interface::move_gripper,this,std::placeholders::_1),{"width","speed"});
    this->_ws_server->bind_method("home_gripper",std::bind(&Interface::home_gripper,this,std::placeholders::_1),{});

    this->_ws_server->bind_method("lockdown_core",std::bind(&Interface::lockdown_core,this,std::placeholders::_1),{});
    this->_ws_server->bind_method("lift_core_lockdown",std::bind(&Interface::lift_core_lockdown,this,std::placeholders::_1),{});

    this->_ws_server->bind_method("set_skill_pause_state",std::bind(&Interface::lift_core_lockdown,this,std::placeholders::_1),{"pause"});

    this->_ws_server->bind_method("teach_object",std::bind(&Interface::teach_object,this,std::placeholders::_1),{"object","teach_width","reference_frame","is_reference_frame"});
    this->_ws_server->bind_method("apply_reference_frame",std::bind(&Interface::apply_reference_frame,this,std::placeholders::_1),{"frame"});
    this->_ws_server->bind_method("download_task_description",std::bind(&Interface::download_task_description,this,std::placeholders::_1),{"task"});
    this->_ws_server->bind_method("download_skill_description",std::bind(&Interface::download_skill_description,this,std::placeholders::_1),{"skill"});
    this->_ws_server->bind_method("download_object_description",std::bind(&Interface::download_object_description,this,std::placeholders::_1),{"object"});

    this->_ws_server->bind_method("get_state",std::bind(&Interface::get_state,this,std::placeholders::_1),{});

    this->_ws_server->bind_method("login_digital_twin",std::bind(&Interface::login_digital_twin,this,std::placeholders::_1),{});
    this->_ws_server->bind_method("logout_digital_twin",std::bind(&Interface::logout_digital_twin,this,std::placeholders::_1),{});

    this->_ws_server->bind_method("reset",std::bind(&Interface::reset,this,std::placeholders::_1),{});

    this->_ws_server->bind_method("unlock_brakes",std::bind(&Interface::unlock_brakes,this,std::placeholders::_1),{});
    this->_ws_server->bind_method("lock_brakes",std::bind(&Interface::lock_brakes,this,std::placeholders::_1),{});
    this->_ws_server->bind_method("shutdown",std::bind(&Interface::shutdown,this,std::placeholders::_1),{});
    this->_ws_server->bind_method("pack_pose",std::bind(&Interface::pack_pose,this,std::placeholders::_1),{});
}

nlohmann::json Interface::start_task(const nlohmann::json &request){
    nlohmann::json response;
    std::pair<bool,std::string> result=this->_task_handler->start_task(request["task"],request["parameters"],request["queue"]);
    if(result.first){
        response["task_uuid"]=result.second;
        response["result"]=true;
    }else{
        response["error"]=result.second;
        response["result"]=false;
    }
    return response;
}

nlohmann::json Interface::stop_task(const nlohmann::json &request){
    nlohmann::json response;
    std::pair<bool,std::string> result;
    result=this->_task_handler->stop_task(request["nominal"],request["success"],request["recover"],request["empty_queue"],request["cost_suc"],request["cost_err"]);
    if(result.first){
        response["result"]=true;
    }else{
        msrm_utils::print_error(result.second);
        response["error"]=result.second;
        response["result"]=false;
    }
    return response;
}

nlohmann::json Interface::remove_task(const nlohmann::json &request){
    nlohmann::json response;
    std::string task_uuid;
    request["task_uuid"].get_to(task_uuid);

    if(this->_task_handler->get_active_task_id()==task_uuid){
        response["error"]="Cannot remove the currently running task.";
        response["result"]=false;
    }else if(this->_task_handler->has_id(task_uuid)){
        std::pair<bool,std::string> result;
        msrm_utils::print_info("Removing task with uuid " + task_uuid + ".");
        result=this->_task_handler->remove_task(task_uuid);
        if(result.first){
            response["result"]=true;
        }else{
            response["error"]=result.second;
            response["result"]=false;
        }
    }else{
        response["error"]="Task uuid " + task_uuid + " is not known to the task scheduler.";
        response["result"]=false;
    }
    return response;
}

nlohmann::json Interface::wait_for_task(const nlohmann::json &request){
    nlohmann::json response;
    std::string task_uuid;
    request["task_uuid"].get_to(task_uuid);
    std::pair<EvalTask,bool> e =this->_task_handler->wait_for_task(task_uuid);
    if(e.second==false){
        msrm_utils::print_error("Could not subscribe to task with uuid "+task_uuid+" or find its evaluation in memory.");
        response["error"]="Could not subscribe to task with uuid "+task_uuid+" or find its evaluation in memory.";
        response["result"]=false;
        response["eval"]=nlohmann::json();
        return response;
    }else{
        response["result"]=true;
        nlohmann::json eval;
        eval["success"]=e.first.success;
        eval["cost_err"]=e.first.cost_err;
        eval["cost_suc"]=e.first.cost_suc;
        eval["nominal_termination"]=e.first.nominal_termination;
        eval["results"]=e.first.results;
        eval["error"]=e.first.last_error;
        response["eval"]=eval;
        return response;
    }
}

nlohmann::json Interface::check_if_task_finished(const nlohmann::json &request){
    nlohmann::json response;
    std::string task_uuid;
    request["task_uuid"].get_to(task_uuid);
    std::pair<EvalTask,bool> e = this->_task_handler->check_if_finished(task_uuid);
    if(e.second==false){
        msrm_utils::print_error("Could not subscribe to task with uuid "+task_uuid+" or find its evaluation in memory.");
        response["error"]="Could not subscribe to task with uuid "+task_uuid+" or find its evaluation in memory.";
        response["finished"]=false;
        response["eval"]=nlohmann::json();
        return response;
    }else{
        response["finished"]=true;
        nlohmann::json eval;
        eval["success"]=e.first.success;
        eval["cost_err"]=e.first.cost_err;
        eval["cost_suc"]=e.first.cost_suc;
        eval["nominal_termination"]=e.first.nominal_termination;
        eval["results"]=e.first.results;
        eval["error"]=e.first.last_error;
        response["eval"]=eval;
        return response;
    }
}

nlohmann::json Interface::is_busy(const nlohmann::json &request){
    nlohmann::json response;
    response["result"]=true;
    response["busy"]=this->_task_handler->is_busy();
    return response;
}

nlohmann::json Interface::set_grasped_object(const nlohmann::json &request){
    nlohmann::json response;
    if(!this->_core->set_grasped_object(request["object"])){
        response["result"]=false;
        response["error"]="Could not set grasped object.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json Interface::grasp_object(const nlohmann::json &request){
    nlohmann::json response;
    if(!this->_core->grasp_object(request["object"],request["width"],request["speed"],request["force"],request["check_width"])){
        response["result"]=false;
        response["error"]="Grasping has failed.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json Interface::grasp(const nlohmann::json &request){
    nlohmann::json response;
    msrm_utils::print_info("Moving gripper");
    if(!this->_core->grasp(request["width"],request["speed"],request["force"])){
        response["result"]=false;
        response["error"]="Could not move gripper.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json Interface::release_object(const nlohmann::json &request){
    msrm_utils::print_info("Releasing object");
    nlohmann::json response;
    if(!this->_core->release_object(request["width"],request["speed"])){
        response["result"]=false;
        response["error"]="Releasing has failed.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json Interface::move_gripper(const nlohmann::json &request){
    nlohmann::json response;
    msrm_utils::print_info("Moving gripper");
    if(!this->_core->move_gripper(request["width"],request["speed"])){
        response["result"]=false;
        response["error"]="Could not move gripper.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json Interface::home_gripper(const nlohmann::json &request){
    nlohmann::json response;
    if(!this->_core->home_gripper()){
        response["result"]=false;
        response["error"]="Homing has failed.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json Interface::lockdown_core(const nlohmann::json &request){
    msrm_utils::print_info("Locking core.");
    this->_core->lockdown();
    return nlohmann::json();
}

nlohmann::json Interface::lift_core_lockdown(const nlohmann::json &request){
    msrm_utils::print_info("Lifting core lockdown.");
    this->_core->lift_lockdown();
    return nlohmann::json();
}

nlohmann::json Interface::set_skill_pause_state(const nlohmann::json &request){
    nlohmann::json response;
    response["result"]=true;
    this->_core->toggle_skill_pause(request["pause"]);
    return response;
}

nlohmann::json Interface::teach_object(const nlohmann::json &request){
    nlohmann::json response;
    try{
        const Percept p=this->_core->request_percept(Eigen::Matrix<double,3,3>::Zero(3,3),true);
        if(!this->_core->get_kb()->teach_object(request["object"],p,request["is_reference_frame"],request["reference_frame"],request["teach_width"])){
            response["result"]=false;
            response["error"]="Object can not be teached.";
        }
    }catch(const CoreException& e){
        std::cout<<e.what()<<std::endl;
        response["error"]=e.what();
        response["result"]=false;
    }
    return response;
}

nlohmann::json Interface::apply_reference_frame(const nlohmann::json &request){
    nlohmann::json response;
    if(!this->_core->get_kb()->apply_reference_frame(request["frame"])){
        response["result"]=false;
        response["error"]="Reference frame could not be applied.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json Interface::download_task_description(const nlohmann::json &request){
    nlohmann::json response, description;
    std::string task;
    request["task"].get_to(task);
    if(this->_core->get_kb()->load_task(task,description)){
        response["description"]=description;
        response["result"]=true;
    }else{
        response["result"]=false;
        response["error"]="Could not download task with name "+task+".";
    }
    return response;
}

nlohmann::json Interface::download_skill_description(const nlohmann::json &request){
    nlohmann::json response, description;
    std::string skill;
    request["skill"].get_to(skill);
    if(this->_core->get_kb()->load_skill(skill,description)){
        response["description"]=description;
        response["result"]=true;
    }else{
        response["result"]=false;
        response["error"]="Could not download skill with name "+skill+".";
    }
    return response;
}

nlohmann::json Interface::download_object_description(const nlohmann::json &request){
    nlohmann::json response, description;
    std::string object;
    request["object"].get_to(object);
    if(this->_core->get_kb()->load_object(object,description)){
        response["description"]=description;
        response["result"]=true;
    }else{
        response["result"]=false;
        response["error"]="Could not download task with name "+object+".";
    }
    return response;
}

nlohmann::json Interface::get_state(const nlohmann::json &request){
    nlohmann::json response;
    try{
        const Percept p = this->_core->request_percept(this->_core->get_kb()->get_local_memory()->access_config_frames().O_R_TF);
        msrm_utils::write_json_array<double,7,1>(response["q"],p.q);
        msrm_utils::write_json_array<double,4,4>(response["O_T_EE"],p.O_T_EE);
        response["grasped_object"]=this->_core->get_mios_state()->grasped_object;
        response["active_task"]=p.mios_state.active_task;
        response["result"]=true;
    }catch(const CoreException& e){
        response["error"]=e.what();
        response["result"]=false;
    }
    return response;
}

nlohmann::json Interface::subscribe_to_event_stream(const nlohmann::json &request){
    nlohmann::json response;
    std::string address;
    unsigned port;
    request["address"].get_to(address);
    request["port"].get_to(port);
    EventPublisher::subscribe(std::pair<std::string,unsigned>(address,port));
    return response;
}

nlohmann::json Interface::unsubscribe_from_event_stream(const nlohmann::json &request){
    nlohmann::json response;
    std::string address;
    unsigned port;
    request["address"].get_to(address);
    request["port"].get_to(port);
    EventPublisher::unsubscribe(std::pair<std::string,unsigned>(address,port));
    return response;
}

nlohmann::json Interface::login_digital_twin(const nlohmann::json &request){
    msrm_utils::print_info("Logging into digital twin.");
    this->_core->login_digital_twin();
    return nlohmann::json();
}

nlohmann::json Interface::logout_digital_twin(const nlohmann::json &request){
    msrm_utils::print_info("Logging out of digital twin.");
    this->_core->logout_digital_twin();
    return nlohmann::json();
}

nlohmann::json Interface::reset(const nlohmann::json &request){
    nlohmann::json response;
    this->_task_handler->set_interrupt(true);
    msrm_utils::print_info("Resetting task handler");
    this->_task_handler->reset();
    msrm_utils::print_info("Resetting core");
    response["result"]=true;
    if(!this->_core->reset()){
        msrm_utils::print_error("Reset failed, could not reinitialize core.");
        response["error"]="Reset failed, could not reinitialize core.";
        response["result"]=false;
    }
    this->_task_handler->set_interrupt(false);
    return response;
}

nlohmann::json Interface::unlock_brakes(const nlohmann::json &request){
    msrm_utils::print_info("Attempting to unlock brakes.");
    this->_core->unlock_brakes();
    return nlohmann::json();
}

nlohmann::json Interface::lock_brakes(const nlohmann::json &request){
    msrm_utils::print_info("Attempting to lock brakes.");
    this->_core->lock_brakes();
    return nlohmann::json();
}

nlohmann::json Interface::shutdown(const nlohmann::json &request){
    msrm_utils::print_info("Attempting to shutdown.");
    this->_core->shutdown_robot();
    return nlohmann::json();
}

nlohmann::json Interface::pack_pose(const nlohmann::json &request){
    nlohmann::json response;
    msrm_utils::print_info("Attempting to move to pack pose.");
    response["error"]="";
    if(this->_core->is_grasping()){
        msrm_utils::print_error("The robot might be holding an object. Moving to pack pose is not safe.");
        response["error"]="The robot might be holding an object. Moving to pack pose is not safe.";
        response["result"]=false;
        return response;
    }
    response["result"]=this->_core->move_to_pack_pose();
    return response;
}

}
