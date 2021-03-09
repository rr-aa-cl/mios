#include "strategies/gripper_strategy.hpp"

namespace mios {

GripperStrategy::GripperStrategy():PrimitiveStrategy({CommandPatternGripper}){
    m_request=GripperRequest::None;
}

void GripperStrategy::initialize(const Percept &p_0){
    m_gripper_finished=false;
}

void GripperStrategy::get_next_command(Actuator &cmd, const Percept &p){
    if(m_request==GripperRequest::Grasp){
        cmd.grasp(m_gripper_width,m_gripper_speed,m_gripper_force,m_gripper_object);
    }
    if(m_request==GripperRequest::Move){
        cmd.move_fingers(m_gripper_width,m_gripper_speed);
    }
    if(p.internal_model.hand_activity_state==HandActivityState::hsFinished){
        m_gripper_finished=true;
    }else{
        m_gripper_finished=false;
    }
}

void GripperStrategy::terminate(const Percept &p){

}

bool GripperStrategy::finished(){
    return m_gripper_finished;
}

void GripperStrategy::grasp(double width, double speed, double force, std::string object){
    m_request=GripperRequest::Grasp;
    m_gripper_width=width;
    m_gripper_speed=speed;
    m_gripper_force=force;
    m_gripper_object=object;
}

void GripperStrategy::move(double width, double speed){
    m_request=GripperRequest::Move;
    m_gripper_width=width;
    m_gripper_speed=speed;
}

}
