#pragma once

#include <ros/ros.h>

namespace mios{

class RosNode{
public:
    RosNode();

    void start();
    void stop();
    ros::NodeHandle* get_node_handle();

private:

private:
    ros::NodeHandle m_node;
    ros::AsyncSpinner m_spinner;
};

}
