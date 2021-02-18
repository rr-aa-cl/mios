#pragma once

#include "strategy/primitive_strategy.hpp"

namespace mios {

class GripperStrategy : public PrimitiveStrategy{
public:
    GripperStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    void grasp(double width, double speed, double force, std::string object);
    void move(double width, double speed);

private:
    GripperRequest m_request;

    double m_gripper_width;
    double m_gripper_speed;
    double m_gripper_force;
    std::string m_gripper_object;

    bool m_gripper_finished;
};

}
