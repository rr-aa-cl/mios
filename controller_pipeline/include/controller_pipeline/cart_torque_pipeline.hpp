#pragma once

#include "controller_pipeline/controller_pipeline.hpp"

#include "plugins/cntr_aic_wrapper.hpp"
#include "plugins/cntr_force_wrapper.hpp"
#include "plugins/cntr_joint_var_imp_wrapper.hpp"
#include "plugins/cntr_mux_wrapper.hpp"
#include "plugins/conv_vel2pose_wrapper.hpp"
#include "plugins/cntr_nullsp_proj_wrapper.hpp"

namespace mios {

class CartTorqueControllerPipeline : public ControllerPipeline{
public:
    CartTorqueControllerPipeline();
    ~CartTorqueControllerPipeline();
    void initialize(const Percept& p_0,Memory* memory) override;
    franka::Finishable* step(const Percept &p, const Actuator &cmd) override;
    bool is_valid_command(const franka::Finishable* const cmd) const;
    void update_percept(Percept::Controller &p) override;
    void terminate() override;
    void context_switch(const Percept &p) override;

private:
    void initialize_cntr_aic(const Percept &p,Memory* memory);
    void initialize_cntr_force(const Percept &p,Memory* memory);
    void initialize_cntr_mux(const Percept &p, Memory *memory);
    void initialize_cntr_nullsp(const Percept &p,Memory* memory);

    void input_cntr_aic(const Percept& p);
    void input_cntr_force(const Percept& p);
    void input_cntr_mux(const Percept& p);
    void input_cntr_nullsp(const Percept& p);

private:
    franka::Torques m_panda_cmd;
    bool m_nullspace_control_on;
    Eigen::Matrix<double,4,4> m_T_T_EE_0;

private:
    cntr_aic::cntr_aic m_cntr_aic;
    cntr_force::cntr_force m_cntr_force;
    cntr_mux::cntr_mux m_cntr_mux;
    conv_vel2pose::conv_vel2pose m_conv_vel2pose;
    cntr_joint_var_imp::cntr_joint_var_imp m_cntr_nullsp_q;
    cntr_nullsp_proj::cntr_nullsp_proj m_cntr_nullsp_proj;
};

}
