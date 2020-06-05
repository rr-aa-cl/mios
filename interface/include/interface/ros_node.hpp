#pragma once

#include "ros/ros.h"

namespace mios{

class RosNode{
public:
    RosNode(int rate);

    void run();
    ros::NodeHandle* get_node_handle();

private:
    ros::NodeHandle m_node;
    int m_rate;
};

}
