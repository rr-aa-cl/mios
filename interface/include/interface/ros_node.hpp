#pragma once

#include <ros/ros.h>
#include "mios_msg/StartTask.h"
#include "mios_msg/StopTask.h"
#include "mios_msg/RemoveTask.h"
#include "mios_msg/WaitForTask.h"
#include "mios_msg/IsBusy.h"
#include "mios_msg/PostEvent.h"
#include "mios_msg/GetEvent.h"
#include "mios_msg/SetGraspedObject.h"
#include "mios_msg/GraspObject.h"
#include "mios_msg/Grasp.h"
#include "mios_msg/ReleaseObject.h"
#include "mios_msg/MoveGripper.h"
#include "mios_msg/HomeGripper.h"
#include "mios_msg/TeachObject.h"
#include "mios_msg/SetObject.h"
#include "mios_msg/DownloadTaskContext.h"
#include "mios_msg/DownloadSkillContext.h"
#include "mios_msg/DownloadObjectContext.h"
#include "mios_msg/GetState.h"
#include "mios_msg/GetModel.h"
#include "mios_msg/StartDeskTask.h"
#include "mios_msg/StopDeskTask.h"
#include "mios_msg/UnlockBrakes.h"
#include "mios_msg/LockBrakes.h"
#include "mios_msg/Shutdown.h"
#include "mios_msg/PackPose.h"
#include "mios_msg/SetLiveParameter.h"
#include "mios_msg/Terminate.h"

namespace mios{

class Core;
class TaskEngine;
class Portal;
class Memory;

class RosNode{
public:
    RosNode(Core *core, TaskEngine *task_engine, Portal *portal, Memory* memory);

    void start();
    void stop();
    ros::NodeHandle* get_node_handle();

private:

    bool start_task(mios_msg::StartTask::Request& request,mios_msg::StartTask::Response& response);
    bool stop_task(mios_msg::StopTask::Request& request,mios_msg::StopTask::Response& response);
    bool remove_task(mios_msg::RemoveTask::Request& request,mios_msg::RemoveTask::Response& response);
    bool wait_for_task(mios_msg::WaitForTask::Request& request,mios_msg::WaitForTask::Response& response);
    bool is_busy(mios_msg::IsBusy::Request& request, mios_msg::IsBusy::Response& response);
    bool post_event(mios_msg::PostEvent::Request& request, mios_msg::PostEvent::Response& response);
    bool get_event(mios_msg::GetEvent::Request& request, mios_msg::GetEvent::Response& response);

    bool set_grasped_object(mios_msg::SetGraspedObject::Request& request, mios_msg::SetGraspedObject::Response& response);
    bool grasp_object(mios_msg::GraspObject::Request& request, mios_msg::GraspObject::Response& response);
    bool grasp(mios_msg::Grasp::Request& request, mios_msg::Grasp::Response& response);
    bool release_object(mios_msg::ReleaseObject::Request& request, mios_msg::ReleaseObject::Response& response);
    bool move_gripper(mios_msg::MoveGripper::Request& request, mios_msg::MoveGripper::Response& response);
    bool home_gripper(mios_msg::HomeGripper::Request& request, mios_msg::HomeGripper::Response& response);

    bool teach_object(mios_msg::TeachObject::Request& request, mios_msg::TeachObject::Response& response);
    bool set_object(mios_msg::SetObject::Request& request, mios_msg::SetObject::Response& response);
    bool download_task_context(mios_msg::DownloadTaskContext::Request& request, mios_msg::DownloadTaskContext::Response& response);
    bool download_skill_context(mios_msg::DownloadSkillContext::Request& request, mios_msg::DownloadSkillContext::Response& response);
    bool download_object_context(mios_msg::DownloadObjectContext::Request& request, mios_msg::DownloadObjectContext::Response& response);

    bool get_state(mios_msg::GetState::Request& request, mios_msg::GetState::Response& response);
    bool get_model(mios_msg::GetModel::Request& request, mios_msg::GetModel::Response& response);

    bool start_desk_task(mios_msg::StartDeskTask::Request& request, mios_msg::StartDeskTask::Response& response);
    bool stop_desk_task(mios_msg::StopDeskTask::Request& request, mios_msg::StopDeskTask::Response& response);
    bool unlock_brakes(mios_msg::UnlockBrakes::Request& request, mios_msg::UnlockBrakes::Response& response);
    bool lock_brakes(mios_msg::LockBrakes::Request& request, mios_msg::LockBrakes::Response& response);
    bool shutdown(mios_msg::Shutdown::Request& request, mios_msg::Shutdown::Response& response);
    bool pack_pose(mios_msg::PackPose::Request& request, mios_msg::PackPose::Response& response);

    bool set_live_parameter(mios_msg::SetLiveParameter::Request& request, mios_msg::SetLiveParameter::Response& response);
    bool terminate(mios_msg::Terminate::Request& request, mios_msg::Terminate::Response& response);

private:
    ros::NodeHandle m_node;
    ros::AsyncSpinner m_spinner;

    Core* m_core;
    TaskEngine* m_task_engine;
    Portal* m_portal;
    Memory* m_memory;

private:
    ros::ServiceServer m_srv_start_task;
    ros::ServiceServer m_srv_stop_task;
    ros::ServiceServer m_srv_remove_task;
    ros::ServiceServer m_srv_wait_for_task;
    ros::ServiceServer m_srv_is_busy;
    ros::ServiceServer m_srv_post_event;
    ros::ServiceServer m_srv_get_event;

    ros::ServiceServer m_srv_set_grasped_object;
    ros::ServiceServer m_srv_grasp_object;
    ros::ServiceServer m_srv_grasp;
    ros::ServiceServer m_srv_release_object;
    ros::ServiceServer m_srv_move_gripper;
    ros::ServiceServer m_srv_home_gripper;

    ros::ServiceServer m_srv_teach_object;
    ros::ServiceServer m_srv_set_object;
    ros::ServiceServer m_srv_download_task_context;
    ros::ServiceServer m_srv_download_skill_context;
    ros::ServiceServer m_srv_download_object_context;

    ros::ServiceServer m_srv_get_state;
    ros::ServiceServer m_srv_get_model;

    ros::ServiceServer m_srv_start_desk_task;
    ros::ServiceServer m_srv_stop_desk_task;
    ros::ServiceServer m_srv_unlock_brakes;
    ros::ServiceServer m_srv_lock_brakes;
    ros::ServiceServer m_srv_shutdown;
    ros::ServiceServer m_srv_pack_pose;

    ros::ServiceServer m_srv_set_live_parameter;
    ros::ServiceServer m_srv_terminate;
};

}
