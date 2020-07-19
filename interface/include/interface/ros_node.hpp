#pragma once

#include <ros/ros.h>
#include "mios_msg/StartTask.h"
#include "mios_msg/StopTask.h"
#include "mios_msg/RemoveTask.h"
#include "mios_msg/WaitForTask.h"
#include "mios_msg/IsBusy.h"

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

private:
    ros::NodeHandle m_node;
    ros::AsyncSpinner m_spinner;

    Core* m_core;
    TaskEngine* m_task_engine;
    Portal* m_portal;
    Memory* m_memory;

private:
    ros::ServiceServer m_srv_start_task;
};

}
