#pragma once

#include "controller_pipeline/controller_pipeline.hpp"

#include "plugins/cntr_joint_var_imp_wrapper.hpp"
#include "plugins/cntr_mux_wrapper.hpp"

namespace mios {

class JointTorqueControllerPipeline : public ControllerPipeline{
public:
    JointTorqueControllerPipeline();
    void initialize(const Percept& p_0,Memory* memory) override;
    franka::Finishable* step(const Percept &p, const Actuator &cmd) override;
    bool is_valid_command(const franka::Finishable* const cmd) const;
    void update_percept(Percept::Controller &p) override;
    void terminate() override;

private:
    void initialize_cntr_joint_imp(const Percept &p,Memory* memory);
    void initialize_cntr_mux(const Percept &p, Memory *memory);

    void input_cntr_joint_imp(const Percept& p);
    void input_cntr_mux(const Percept& p);

private:
    franka::Torques m_panda_cmd;
    Eigen::Matrix<double,7,1> m_q_d_old;

private:
    cntr_mux::cntr_mux m_cntr_mux;
    cntr_joint_var_imp::cntr_joint_var_imp m_cntr_joint_imp;
};

}
