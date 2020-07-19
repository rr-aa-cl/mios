#include "interface/ros_node.hpp"
#include "core/core.hpp"
#include "task/task_engine.hpp"
#include "portal/portal.hpp"
#include "memory/memory.hpp"
#include <functional>

namespace mios {

RosNode::RosNode(Core *core, TaskEngine *task_engine, Portal *portal, Memory* memory):m_spinner(4),m_core(core),m_task_engine(task_engine),m_portal(portal),m_memory(memory){
    m_srv_start_task = m_node.advertiseService("start_task",&RosNode::start_task,this);
}

void RosNode::start(){
    m_spinner.start();
}

void RosNode::stop(){
    m_spinner.stop();
}

bool RosNode::start_task(mios_msg::StartTask::Request &request, mios_msg::StartTask::Response &response){
    spdlog::debug("RosNode: start_task");
    nlohmann::json response_json;
    bool result;
    std::string task_uuid;
    std::string error_message;
    std::tie(result,task_uuid,error_message)=m_task_engine->start_task(request.task,nlohmann::json::parse(request.parameters),request.queue);
    response.task_uuid=task_uuid;
    response.error_message=error_message;
    response.result=result;
    return true;
}

bool RosNode::stop_task(mios_msg::StopTask::Request &request, mios_msg::StopTask::Response &response){
    spdlog::debug("RosNode: stop_task");
    std::string error_message;
    std::tie(response.result,response.error_message)=m_task_engine->stop_task(request.raise_exception,request.recover,request.empty_queue);
    return true;
}

bool RosNode::remove_task(mios_msg::RemoveTask::Request &request, mios_msg::RemoveTask::Response &response){
    spdlog::debug("RosNode: remove_task");

    spdlog::info("Removing task with uuid " + request.task_uuid + ".");
    std::tie(response.result,response.error_message)=m_task_engine->remove_task(request.task_uuid);
    return true;
}

bool RosNode::wait_for_task(mios_msg::WaitForTask::Request &request, mios_msg::WaitForTask::Response &response){
    spdlog::debug("RosNode: wait_for_task");
    std::string task_uuid;
    bool result;
    std::string error_message;
    TaskResult task_result;
    std::tie(response.result,task_result,response.error_message)=m_task_engine->wait_for_task(request.task_uuid);
    nlohmann::json task_result_response;
    if(result){
        task_result_response["success"]=task_result.success;
        task_result_response["cost_err"]=task_result.cost_err;
        task_result_response["cost_suc"]=task_result.cost_suc;
        task_result_response["external_stop"]=task_result.external_stop;
        task_result_response["exception"]=task_result.exception;
        task_result_response["results"]=task_result.custom_results;
        task_result_response["error"]=task_result.errors;
    }else{
        task_result_response["success"]=false;
        task_result_response["cost_err"]=0;
        task_result_response["cost_suc"]=0;
        task_result_response["external_stop"]=false;
        task_result_response["exception"]=true;
        task_result_response["results"]=nlohmann::json();
        task_result_response["error"]={};
    }
    response.task_result=task_result_response.dump();
    return true;
}

bool RosNode::is_busy(mios_msg::IsBusy::Request &request, mios_msg::IsBusy::Response &response){
    spdlog::debug("RosNode: is_busy");
    response.busy=m_task_engine->is_busy();
    response.result=true;
    return true;
}

}
