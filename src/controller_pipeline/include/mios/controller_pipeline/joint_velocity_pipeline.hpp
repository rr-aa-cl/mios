#pragma once

#include "controller_pipeline/controller_pipeline.hpp"

namespace mios {

class JointVelocityControllerPipeline : public ControllerPipeline{
public:
    JointVelocityControllerPipeline();
    void initialize(const Percept& p_0,Memory* memory) override;
    franka::Finishable* step(const Percept &p, const Actuator &cmd) override;
    bool is_valid_command(const franka::Finishable* const cmd) const;
    void update_percept(Percept::Controller &p) override;
    void terminate() override;
    void context_switch(const Percept &p) override;
private:
    franka::JointVelocities m_panda_cmd;
    Eigen::Matrix<double,7,1> m_q_d_old;
};

}
