#include "interface/ros_node.hpp"
#include "core/core.hpp"
#include "task/task_engine.hpp"
#include "portal/portal.hpp"
#include "memory/memory.hpp"
#include <functional>
#include "msrm_utils/conversion.hpp"

namespace mios {

RosNode::RosNode(Core *core, TaskEngine *task_engine, Portal *portal, Memory* memory):m_spinner(4),m_core(core),m_task_engine(task_engine),m_portal(portal),m_memory(memory){
    m_srv_start_task = m_node.advertiseService("start_task",&RosNode::start_task,this);
    m_srv_stop_task = m_node.advertiseService("stop_task",&RosNode::stop_task,this);
    m_srv_remove_task = m_node.advertiseService("remove_task",&RosNode::remove_task,this);
    m_srv_wait_for_task = m_node.advertiseService("wait_for_task",&RosNode::wait_for_task,this);
    m_srv_is_busy = m_node.advertiseService("is_busy",&RosNode::is_busy,this);
    m_srv_post_event = m_node.advertiseService("post_event",&RosNode::post_event,this);
    m_srv_get_event = m_node.advertiseService("get_event",&RosNode::get_event,this);

    m_srv_set_grasped_object = m_node.advertiseService("set_grasped_object",&RosNode::set_grasped_object,this);
    m_srv_grasp_object = m_node.advertiseService("grasp_object",&RosNode::grasp_object,this);
    m_srv_grasp= m_node.advertiseService("grasp",&RosNode::grasp,this);
    m_srv_release_object = m_node.advertiseService("release_object",&RosNode::release_object,this);
    m_srv_move_gripper = m_node.advertiseService("move_gripper",&RosNode::move_gripper,this);
    m_srv_home_gripper = m_node.advertiseService("home_gripper",&RosNode::home_gripper,this);

    m_srv_teach_object = m_node.advertiseService("teach_object",&RosNode::teach_object,this);
    m_srv_set_object = m_node.advertiseService("set_object",&RosNode::set_object,this);
    m_srv_download_task_context = m_node.advertiseService("download_task_context",&RosNode::download_task_context,this);
    m_srv_download_skill_context = m_node.advertiseService("download_skill_context",&RosNode::download_skill_context,this);
    m_srv_download_object_context = m_node.advertiseService("download_object_context",&RosNode::download_object_context,this);

    m_srv_get_state = m_node.advertiseService("get_state",&RosNode::get_state,this);
    m_srv_get_model = m_node.advertiseService("get_model",&RosNode::get_model,this);

    m_srv_start_desk_task = m_node.advertiseService("start_desk_task",&RosNode::start_desk_task,this);
    m_srv_stop_desk_task = m_node.advertiseService("stop_desk_task",&RosNode::stop_desk_task,this);
    m_srv_unlock_brakes = m_node.advertiseService("unlock_brakes",&RosNode::unlock_brakes,this);
    m_srv_lock_brakes = m_node.advertiseService("lock_brakes",&RosNode::lock_brakes,this);
    m_srv_shutdown = m_node.advertiseService("shutdown",&RosNode::shutdown,this);
    m_srv_pack_pose = m_node.advertiseService("pack_pose",&RosNode::pack_pose,this);

    m_srv_set_live_parameter = m_node.advertiseService("set_live_parameter",&RosNode::set_live_parameter,this);
    m_srv_terminate = m_node.advertiseService("terminate",&RosNode::terminate,this);
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
    if(response.result){
        task_result_response["success"]=task_result.success;
        task_result_response["external_stop"]=task_result.external_stop;
        task_result_response["exception"]=task_result.exception;
        task_result_response["results"]=task_result.custom_results;
        task_result_response["error"]=task_result.errors;
    }else{
        task_result_response["success"]=false;
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

bool RosNode::post_event(mios_msg::PostEvent::Request &request, mios_msg::PostEvent::Response &response){
    m_memory->post_event(request.name,request.content);
    response.result=true;
    return true;
}

bool RosNode::get_event(mios_msg::GetEvent::Request &request, mios_msg::GetEvent::Response &response){
    response.content=m_memory->get_event(request.name)->get_content().dump();
    return true;
}

bool RosNode::set_grasped_object(mios_msg::SetGraspedObject::Request &request, mios_msg::SetGraspedObject::Response &response){
    if(!m_core->set_grasped_object(request.object)){
        response.error_message="Could not set grasped object.";
        response.result=false;
    }else{
        response.error_message="";
        response.result=true;
    }
    return true;
}

bool RosNode::grasp_object(mios_msg::GraspObject::Request &request, mios_msg::GraspObject::Response &response){
    if(!m_core->grasp_object(request.object,request.speed)){
        response.error_message="Grasping has failed.";
        response.result=false;
    }else{
        response.error_message="";
        response.result=true;
    }
    return true;
}

bool RosNode::grasp(mios_msg::Grasp::Request &request, mios_msg::Grasp::Response &response){
    if(!m_core->grasp(request.width,request.speed,request.force,request.epsilon_inner,request.epsilon_outer)){
        response.error_message="Grasping has failed.";
        response.result=false;
    }else{
        response.error_message="";
        response.result=true;
    }
    return true;
}

bool RosNode::release_object(mios_msg::ReleaseObject::Request &request, mios_msg::ReleaseObject::Response &response){
    if(!m_core->release_object(request.speed)){
        response.error_message="Releasing has failed.";
        response.result=false;
    }else{
        response.error_message="";
        response.result=true;
    }
    return true;
}

bool RosNode::move_gripper(mios_msg::MoveGripper::Request &request, mios_msg::MoveGripper::Response &response){
    if(!m_core->move_gripper(request.width,request.speed)){
        response.error_message="Could not move gripper.";
        response.result=false;
    }else{
        response.error_message="";
        response.result=true;
    }
    return true;
}

bool RosNode::home_gripper(mios_msg::HomeGripper::Request &request, mios_msg::HomeGripper::Response &response){
    if(!m_core->home_gripper()){
        response.error_message="Homing has failed.";
        response.result=false;
    }else{
        response.error_message="";
        response.result=true;
    }
    return true;
}

bool RosNode::teach_object(mios_msg::TeachObject::Request &request, mios_msg::TeachObject::Response &response){
    response.error_message="";
    response.result=true;
    if(!m_core->refresh_percept({})){
        response.error_message="Could not teach the object because no current percept is available.";
        response.result=false;
    }
    if(!m_memory->update_object(request.object,request.teach_width,*m_core->get_percept())){
        response.error_message="Could not teach the object because the memory returned an error.";
        response.result=false;
    }
    return true;
}

bool RosNode::set_object(mios_msg::SetObject::Request &request, mios_msg::SetObject::Response &response){
    nlohmann::json description={
        {"O_T_OB",request.O_T_OB},
        {"OB_T_gp",request.OB_T_gp},
        {"OB_T_TCP",request.OB_T_TCP},
        {"OB_I",request.OB_I},
        {"q",request.q},
        {"grasp_width",request.grasp_width},
        {"grasp_force",request.grasp_force},
        {"mass",request.mass},
        {"geometry",request.geometry}
    };
    bool result = m_memory->update_object(request.name,description);
    response.error_message="";
    response.result=true;
    if(!result){
        response.error_message="Could not update object with name " + request.name;
        response.result=false;
    }
    return true;
}

bool RosNode::download_task_context(mios_msg::DownloadTaskContext::Request &request, mios_msg::DownloadTaskContext::Response &response){
    nlohmann::json context;
    if(m_core->get_memory()->load_default_task_context(request.task,context)){
        response.context=context.dump();
        response.result=true;
        response.error_message="";
    }else{
        response.result=false;
        response.error_message="Could not download task with name "+request.task+".";
    }
    return true;
}

bool RosNode::download_skill_context(mios_msg::DownloadSkillContext::Request &request, mios_msg::DownloadSkillContext::Response &response){
    nlohmann::json context;
    if(m_core->get_memory()->load_default_skill_context(request.skill,context)){
        response.context=context.dump();
        response.result=true;
        response.error_message="";
    }else{
        response.result=false;
        response.error_message="Could not download skill with name "+request.skill+".";
    }
    return true;
}

bool RosNode::download_object_context(mios_msg::DownloadObjectContext::Request &request, mios_msg::DownloadObjectContext::Response &response){
    const Object* o = m_core->get_memory()->get_object(request.object);
    if(o->name!="NullObject"){
        response.context=o->to_json().dump();
        response.result=true;
        response.error_message="";
    }else{
        response.result=false;
        response.error_message="Could not download object with name "+request.object+".";
    }
    return true;
}

bool RosNode::get_state(mios_msg::GetState::Request &request, mios_msg::GetState::Response &response){
    response.error_message="";
    response.result=true;
    if(!m_core->refresh_percept({})){
        response.error_message="No current state available, could not refresh perception.";
        response.result=false;
    }
    const Percept* p = m_core->get_percept();
    std::array<double,7> q=msrm_utils::convert_to_array<double,7,1>(p->proprioception.q);
    std::array<double,16> O_T_EE=msrm_utils::convert_to_array<double,4,4>(p->proprioception.O_T_EE);
    response.q=std::vector<float>(q.begin(),q.end());
    response.O_T_EE=std::vector<float>(O_T_EE.begin(),O_T_EE.end());
    response.grasped_object=m_memory->get_live_context()->grasped_object->name;
    return true;
}

bool RosNode::get_model(mios_msg::GetModel::Request &request, mios_msg::GetModel::Response &response){
    response.error_message="";
    response.result=true;
    if(!m_core->refresh_percept({})){
        response.error_message="No current state available, could not refresh perception.";
        response.result=false;
    }
    const Percept* p = m_core->get_percept();
    std::array<double,49> M=msrm_utils::convert_to_array<double,7,7>(p->internal_model.M);
    std::array<double,7> C=msrm_utils::convert_to_array<double,7,1>(p->internal_model.C);
    std::array<double,7> G=msrm_utils::convert_to_array<double,7,1>(p->internal_model.G);
    std::array<double,42> B_J_O=msrm_utils::convert_to_array<double,6,7>(p->internal_model.B_J_O);
    std::array<double,42> B_J_EE=msrm_utils::convert_to_array<double,6,7>(p->internal_model.B_J_EE);
    response.M=std::vector<float>(M.begin(),M.end());
    response.C=std::vector<float>(C.begin(),C.end());
    response.G=std::vector<float>(G.begin(),G.end());
    response.B_J_O=std::vector<float>(B_J_O.begin(),B_J_O.end());
    response.B_J_EE=std::vector<float>(B_J_EE.begin(),B_J_EE.end());
    return true;
}

bool RosNode::start_desk_task(mios_msg::StartDeskTask::Request &request, mios_msg::StartDeskTask::Response &response){
    response.result=m_core->start_desk_task(request.task);
    return true;
}

bool RosNode::stop_desk_task(mios_msg::StopDeskTask::Request &request, mios_msg::StopDeskTask::Response &response){
    response.result=m_core->stop_desk_task();
    return true;
}

bool RosNode::unlock_brakes(mios_msg::UnlockBrakes::Request &request, mios_msg::UnlockBrakes::Response &response){
    response.result=m_core->unlock_body();
    return true;
}

bool RosNode::lock_brakes(mios_msg::LockBrakes::Request &request, mios_msg::LockBrakes::Response &response){
    response.result=m_core->lock_body();
    return true;
}

bool RosNode::shutdown(mios_msg::Shutdown::Request &request, mios_msg::Shutdown::Response &response){
    response.result=m_core->shutdown_body();
    return true;
}

bool RosNode::pack_pose(mios_msg::PackPose::Request &request, mios_msg::PackPose::Response &response){
    response.result=m_core->pack_body();
    return true;
}

bool RosNode::set_live_parameter(mios_msg::SetLiveParameter::Request &request, mios_msg::SetLiveParameter::Response &response){
    response.error_message="";
    response.result=true;
    m_memory->set_live_parameter(request.key,request.value);
    return true;
}

bool RosNode::terminate(mios_msg::Terminate::Request &request, mios_msg::Terminate::Response &response){
    m_task_engine->stop();
    return true;
}

}
