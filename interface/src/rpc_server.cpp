#include "interface/rpc_server.hpp"

#include <ifaddrs.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <list>

#include "core/core.hpp"
#include "task/task_handler.hpp"

#include "cpp_utils/network.hpp"

namespace mios {

RPCServer::RPCServer(jsonrpccxx::JsonRpc2Server& rpc_server){

    //    this->_rpc_server=rpc_server;

    // task level

    rpc_server.Add("start_task", jsonrpccxx::GetHandle(&RPCServer::start_task, *this),{"task","queue","parameters"});
    rpc_server.Add("stop_task", jsonrpccxx::GetHandle(&RPCServer::stop_task, *this),{"nominal","success","recover", "empty_queue", "cost_suc", "cost_err"});
    rpc_server.Add("remove_task", jsonrpccxx::GetHandle(&RPCServer::remove_task, *this),{"task_uuid"});
    rpc_server.Add("wait_for_task", jsonrpccxx::GetHandle(&RPCServer::wait_for_task, *this),{"task_uuid"});
    rpc_server.Add("check_if_finished", jsonrpccxx::GetHandle(&RPCServer::check_if_finished, *this),{"task_uuid"});
    rpc_server.Add("is_busy", jsonrpccxx::GetHandle(&RPCServer::is_busy, *this));

    rpc_server.Add("set_grasped_object", jsonrpccxx::GetHandle(&RPCServer::set_grasped_object, *this),{"object"});
    rpc_server.Add("grasp_object", jsonrpccxx::GetHandle(&RPCServer::grasp_object, *this),{"object","width","speed","force","check_width"});
    rpc_server.Add("grasp", jsonrpccxx::GetHandle(&RPCServer::grasp, *this),{"width","speed","force"});
    rpc_server.Add("release_object", jsonrpccxx::GetHandle(&RPCServer::release_object, *this),{"width","speed"});
    rpc_server.Add("home_gripper", jsonrpccxx::GetHandle(&RPCServer::home_gripper, *this));
    rpc_server.Add("move_gripper", jsonrpccxx::GetHandle(&RPCServer::move_gripper, *this),{"width","speed"});

    rpc_server.Add("lockdown_core", jsonrpccxx::GetHandle(&RPCServer::lockdown_core, *this));
    rpc_server.Add("lift_core_lockdown", jsonrpccxx::GetHandle(&RPCServer::lift_core_lockdown, *this));

    rpc_server.Add("toggle_skill_pause", jsonrpccxx::GetHandle(&RPCServer::set_skill_pause_state, *this));

    rpc_server.Add("teach_object", jsonrpccxx::GetHandle(&RPCServer::teach_object, *this),{"object","teach_width","reference_frame","is_reference_frame"});
    rpc_server.Add("apply_reference_frame", jsonrpccxx::GetHandle(&RPCServer::apply_reference_frame, *this),{"frame"});
    rpc_server.Add("download_task_description", jsonrpccxx::GetHandle(&RPCServer::download_task_description, *this),{"task"});
    rpc_server.Add("download_skill_description", jsonrpccxx::GetHandle(&RPCServer::download_skill_description, *this),{"skill"});
    rpc_server.Add("download_object_description", jsonrpccxx::GetHandle(&RPCServer::download_object_description, *this),{"object"});

    rpc_server.Add("get_state", jsonrpccxx::GetHandle(&RPCServer::get_state, *this));
    rpc_server.Add("reset", jsonrpccxx::GetHandle(&RPCServer::reset, *this));

    rpc_server.Add("login_digital_twin", jsonrpccxx::GetHandle(&RPCServer::login_digital_twin, *this));
    rpc_server.Add("logout_digital_twin", jsonrpccxx::GetHandle(&RPCServer::logout_digital_twin, *this));

    rpc_server.Add("unlock_brakes", jsonrpccxx::GetHandle(&RPCServer::unlock_brakes, *this));
    rpc_server.Add("lock_brakes", jsonrpccxx::GetHandle(&RPCServer::lock_brakes, *this));
    rpc_server.Add("shutdown", jsonrpccxx::GetHandle(&RPCServer::shutdown, *this));
    rpc_server.Add("pack_pose", jsonrpccxx::GetHandle(&RPCServer::pack_pose, *this));

}

RPCServer::~RPCServer(){
    delete this->_rpc_server;
}

void RPCServer::setup(Core *core, TaskHandler *task_handler){
    this->_core=core;
    this->_task_handler=task_handler;
}

nlohmann::json RPCServer::get_state(){
    nlohmann::json response;
    try{
        const Percept p = this->_core->request_percept(this->_core->get_kb()->get_local_memory()->access_config_frames().O_R_TF);
        cpp_utils::write_json_array<double,7,1>(response["q"],p.q);
        cpp_utils::write_json_array<double,4,4>(response["O_T_EE"],p.O_T_EE);
        response["active_task"]=p.mios_state.active_task;
        response["result"]=true;
    }catch(const CoreException& e){
        response["error"]=e.what();
        response["result"]=false;
    }
    return response;
}

nlohmann::json RPCServer::wait_for_task(const std::string task_uuid){
    nlohmann::json response;
    std::pair<EvalTask,bool> e =this->_task_handler->wait_for_task(task_uuid);
    if(e.second==false){
        cpp_utils::print_error("Could not subscribe to task with uuid "+task_uuid+" or find its evaluation in memory.");
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

nlohmann::json RPCServer::check_if_finished(const std::string task_uuid){
    nlohmann::json response;
    std::pair<EvalTask,bool> e = this->_task_handler->check_if_finished(task_uuid);
    if(e.second==false){
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

nlohmann::json RPCServer::is_busy(){
    nlohmann::json response;
    response["result"]=true;
    response["busy"]=this->_task_handler->is_busy();
    return response;
}

nlohmann::json RPCServer::set_skill_pause_state(const bool pause){
    nlohmann::json response;
    response["result"]=true;
    this->_core->toggle_skill_pause(pause);
    return response;
}

nlohmann::json RPCServer::unlock_brakes(){
    cpp_utils::print_info("Attempting to unlock brakes.");
    this->_core->unlock_brakes();
    return nlohmann::json();
}

nlohmann::json RPCServer::lock_brakes(){
    cpp_utils::print_info("Attempting to lock brakes.");
    this->_core->lock_brakes();
    return nlohmann::json();
}

nlohmann::json RPCServer::shutdown(){
    cpp_utils::print_info("Attempting to shutdown.");
    this->_core->shutdown_robot();
    return nlohmann::json();
}

nlohmann::json RPCServer::pack_pose(){
    nlohmann::json response;
    cpp_utils::print_info("Attempting to move to pack pose.");
    response["error"]="";
    if(this->_core->is_grasping()){
        cpp_utils::print_error("The robot might be holding an object. Moving to pack pose is not safe.");
        response["error"]="The robot might be holding an object. Moving to pack pose is not safe.";
        response["result"]=false;
        return response;
    }
    response["result"]=this->_core->move_to_pack_pose();
    return response;
}

nlohmann::json RPCServer::reset(){
    nlohmann::json response;
    this->_task_handler->set_interrupt(true);
    cpp_utils::print_info("Resetting task handler");
    this->_task_handler->reset();
    cpp_utils::print_info("Resetting core");
    response["result"]=true;
    if(!this->_core->reset()){
        cpp_utils::print_error("Reset failed, could not reinitialize core.");
        response["error"]="Reset failed, could not reinitialize core.";
        response["result"]=false;
    }
    this->_task_handler->set_interrupt(false);
    return response;
}

nlohmann::json RPCServer::start_task(const std::string task, const bool queue, const nlohmann::json& parameters){
    nlohmann::json response;
    std::pair<bool,std::string> result=this->_task_handler->start_task(task,parameters,queue);
    if(result.first){
        response["task_uuid"]=result.second;
        response["result"]=true;
    }else{
        response["error"]=result.second;
        response["result"]=false;
    }
    return response;
}

nlohmann::json RPCServer::stop_task(const bool nominal, const bool success, const bool recover, const bool empty_queue, const double cost_suc, const double cost_err){
    nlohmann::json response;
    std::pair<bool,std::string> result;
    result=this->_task_handler->stop_task(nominal,success,recover,empty_queue,cost_suc,cost_err);
    if(result.first){
        response["result"]=true;
        cpp_utils::print_info("Task has been stopped.");
    }else{
        cpp_utils::print_error(result.second);
        response["error"]=result.second;
        response["result"]=false;
    }
    return response;
}

nlohmann::json RPCServer::remove_task(const std::string task_uuid){
    nlohmann::json response;

    if(this->_task_handler->get_active_task_id()==task_uuid){
        response["error"]="Cannot remove the currently running task.";
        response["result"]=false;
    }else if(this->_task_handler->has_id(task_uuid)){
        std::pair<bool,std::string> result;
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

nlohmann::json RPCServer::set_grasped_object(std::string object){
    nlohmann::json response;
    if(!this->_core->set_grasped_object(object)){
        response["result"]=false;
        response["error"]="Could not set grasped object.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json RPCServer::grasp_object(std::string object, const double width, const double speed, const double force, const bool check_width){
    nlohmann::json response;
    if(!this->_core->grasp_object(object,width,speed,force,check_width)){
        response["result"]=false;
        response["error"]="Grasping has failed.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json RPCServer::release_object(double width, double speed){
    cpp_utils::print_info("Releasing object");
    nlohmann::json response;
    if(!this->_core->release_object(width,speed)){
        response["result"]=false;
        response["error"]="Releasing has failed.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json RPCServer::home_gripper(){
    nlohmann::json response;
    if(!this->_core->home_gripper()){
        response["result"]=false;
        response["error"]="Homing has failed.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json RPCServer::move_gripper(double width, double speed){
    nlohmann::json response;
    cpp_utils::print_info("Moving gripper");
    if(!this->_core->move_gripper(width,speed)){
        response["result"]=false;
        response["error"]="Could not move gripper.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json RPCServer::grasp(double width, double speed, double force){
    nlohmann::json response;
    cpp_utils::print_info("Moving gripper");
    if(!this->_core->grasp(width,speed,force)){
        response["result"]=false;
        response["error"]="Could not move gripper.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json RPCServer::login_digital_twin(){
    cpp_utils::print_info("Logging into digital twin.");
    this->_core->login_digital_twin();
    return nlohmann::json();
}

nlohmann::json RPCServer::logout_digital_twin(){
    cpp_utils::print_info("Logging out of digital twin.");
    this->_core->logout_digital_twin();
    return nlohmann::json();
}

nlohmann::json RPCServer::lockdown_core(){
    cpp_utils::print_info("Locking core.");
    this->_core->lockdown();
    return nlohmann::json();
}

nlohmann::json RPCServer::lift_core_lockdown(){
    cpp_utils::print_info("Lifting core lockdown.");
    this->_core->lift_lockdown();
    return nlohmann::json();
}

nlohmann::json RPCServer::teach_object(const std::string object, const bool teach_width, const std::string reference_frame, const bool is_reference_frame){
    nlohmann::json response;
    try{
        const Percept p=this->_core->request_percept(Eigen::Matrix<double,3,3>::Zero(3,3),true);
        if(!this->_core->get_kb()->teach_object(object,p,is_reference_frame,reference_frame,teach_width)){
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

nlohmann::json RPCServer::apply_reference_frame(const std::string frame){
    nlohmann::json response;
    if(!this->_core->get_kb()->apply_reference_frame(frame)){
        response["result"]=false;
        response["error"]="Reference frame could not be applied.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json RPCServer::download_task_description(const std::string task){
    nlohmann::json response, description;
    if(this->_core->get_kb()->load_task(task,description)){
        response["description"]=description;
        response["result"]=true;
    }else{
        response["result"]=false;
        response["error"]="Could not download task with name "+task+".";
    }
    return response;
}

nlohmann::json RPCServer::download_skill_description(const std::string skill){
    nlohmann::json response, description;
    if(this->_core->get_kb()->load_skill(skill,description)){
        response["description"]=description;
        response["result"]=true;
    }else{
        response["result"]=false;
        response["error"]="Could not download skill with name "+skill+".";
    }
    return response;
}

nlohmann::json RPCServer::download_object_description(const std::string object){
    nlohmann::json response, description;
    if(this->_core->get_kb()->load_object(object,description)){
        response["description"]=description;
        response["result"]=true;
    }else{
        response["result"]=false;
        response["error"]="Could not download task with name "+object+".";
    }
    return response;
}

}
