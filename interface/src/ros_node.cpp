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
    response_json["task_uuid"]=task_uuid;
    response_json["error"]=error_message;
    response_json["result"]=result;
    response.result=response_json.dump();
    return true;
}

}
