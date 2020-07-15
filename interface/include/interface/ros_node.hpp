#pragma once

#include <ros/ros.h>
#include "mios_msg/StartTask.h"

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
