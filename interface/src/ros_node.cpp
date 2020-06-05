#include "interface/ros_node.hpp"

namespace mios {

RosNode::RosNode(int rate):m_rate(rate){

}

void RosNode::run(){
    ros::Rate rate(m_rate);
    while(ros::ok()){
        ros::spinOnce();
        rate.sleep();
    }
}

}
